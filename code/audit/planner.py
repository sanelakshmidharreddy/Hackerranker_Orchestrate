"""
Step planner and serializer.

Given the reconstructed state dict and policy, produces the ordered list of
Step objects per the problem contract:
  Phase: FINDING -> REMEDIATION -> VERIFICATION
  Sort key within phase: (OP_ORDER index, system_id, resource_id)

For COMPLETE cases: only VERIFICATION steps with real evidence_id.
For INCOMPLETE cases: FINDING (with evidence_id) + REMEDIATION (evidence_id="") + VERIFICATION (evidence_id="").
For NOT_APPLICABLE cases: empty step list.

Key rules:
- BACKUP_ARCHIVE -> RETAIN + BLOCK_RESTORE (not delete).
- DATA_FLOW -> DISABLE_DATA_FLOW before deleting dependent records.
- ACCOUNT_TOMBSTONE -> REDACT (keep user_id, remove PII).
- SECURITY_AUDIT_LOG / LEGAL_HOLD_RECORD -> RETAIN (VERIFY_RECORD_PRESENT).
- Active data flows get REPORT_ACTIVE_DATA_FLOW + DISABLE_DATA_FLOW + VERIFY_DATA_FLOW_DISABLED.
- Restorable backups get REPORT_RESTORE_RISK + BLOCK_RESTORE + VERIFY_RESTORE_BLOCKED.
- Recreated records: add finding + remediation even if latest status might look absent.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from config import OP_ORDER, OPERATION_STATE_MAP, PHASE_ORDER
from audit.state import ResourceState
from audit.policy import (
    required_action,
    action_to_finding_operation,
    action_to_remediation_operation,
    action_to_verification_operation,
    canonical_category,
)


@dataclass
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

    def to_dict(self) -> dict:
        return {
            "step_no": self.step_no,
            "phase": self.phase,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "state": self.state,
            "evidence_id": self.evidence_id,
        }


def _op_sort_key(operation: str) -> int:
    try:
        return OP_ORDER.index(operation)
    except ValueError:
        return 99


def _sort_steps(steps: List[Step]) -> List[Step]:
    """Sort steps by (phase_order, op_table_index, system_id, resource_id)."""
    return sorted(
        steps,
        key=lambda s: (
            PHASE_ORDER.get(s.phase, 9),
            _op_sort_key(s.operation),
            s.system_id or "",
            s.resource_id or "",
        ),
    )


# Statuses that indicate a record still needs action (not already in required state)
_NEEDS_DELETION = {"PRESENT", "EXPOSED", "RESTORABLE"}
_NEEDS_REDACTION = {"PRESENT", "EXPOSED"}
_NEEDS_ANONYMIZATION = {"PRESENT", "EXPOSED"}
_NEEDS_DISABLE = {"ACTIVE"}
_NEEDS_BLOCK = {"RESTORABLE"}

# Statuses that are already in the required final state
_IS_ABSENT = {"ABSENT"}
_IS_REDACTED = {"REDACTED"}
_IS_ANONYMIZED = {"ANONYMIZED"}
_IS_RETAINED = {"RETAINED", "PRESENT"}  # retained records should be PRESENT
_IS_DISABLED = {"DISABLED"}
_IS_BLOCKED = {"BLOCKED"}


def plan_steps(
    states: Dict[str, ResourceState],
    policy: Dict[str, str],
    is_shared_support: Optional[callable] = None,
) -> tuple:
    """
    Generate (finding_steps, remediation_steps, verification_steps, overall_complete).

    Args:
        states: resource_id -> ResourceState
        policy: category -> action map
        is_shared_support: optional callable(resource_id) -> bool for rule_05/06 distinction

    Returns:
        (findings, remediations, verifications, is_complete)
    """
    findings: List[Step] = []
    remediations: List[Step] = []
    verifications: List[Step] = []

    for rid, rs in states.items():
        cat = canonical_category(rs.record_type)

        # Determine if support message is shared conversation (rule_05) or attachment-only (rule_06)
        shared = False
        if cat in ("SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT"):
            if is_shared_support:
                shared = is_shared_support(rid)
            else:
                # Default: treat as shared conversation (REDACT) to be safe
                shared = (cat == "SUPPORT_MESSAGE")

        action = required_action(rs.record_type, policy, is_shared_conversation=shared)
        status = rs.status

        # Special status normalization
        # CLAIM statuses: strip CLAIM_ prefix to get underlying status
        if status.startswith("CLAIM_"):
            underlying = status[6:]  # e.g. CLAIM_ABSENT -> ABSENT
            # Treat as claim — the record may or may not have that status
            # Treat CLAIM_ABSENT as ABSENT only when no non-claim proof overrides
            if rs.is_claim:
                status = underlying
            else:
                status = underlying  # non-claim proof was already applied in state reconstruction

        # --- DATA_FLOW ---
        if cat == "DATA_FLOW" or status == "ACTIVE" and action == "DISABLE":
            if status == "ACTIVE":
                # Finding
                findings.append(Step(
                    step_no=0, phase="FINDING",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REPORT_ACTIVE_DATA_FLOW", state="ACTIVE",
                    evidence_id=rs.proof_source_id if not rs.is_claim else "",
                ))
                # Remediation
                remediations.append(Step(
                    step_no=0, phase="REMEDIATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="DISABLE_DATA_FLOW", state="DISABLED",
                    evidence_id="",
                ))
                # Verification
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_DATA_FLOW_DISABLED", state="DISABLED",
                    evidence_id="",
                ))
            elif status == "DISABLED":
                # Already disabled — verification only
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_DATA_FLOW_DISABLED", state="DISABLED",
                    evidence_id=rs.proof_source_id,
                ))
            continue

        # --- BACKUP_ARCHIVE ---
        if cat == "BACKUP_ARCHIVE":
            if status in ("RESTORABLE", "ACTIVE", "PRESENT"):
                # Finding
                findings.append(Step(
                    step_no=0, phase="FINDING",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REPORT_RESTORE_RISK", state="ACTIVE",
                    evidence_id=rs.proof_source_id if not rs.is_claim else "",
                ))
                # Remediation
                remediations.append(Step(
                    step_no=0, phase="REMEDIATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="BLOCK_RESTORE", state="BLOCKED",
                    evidence_id="",
                ))
                # Verification
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RESTORE_BLOCKED", state="BLOCKED",
                    evidence_id="",
                ))
            elif status == "BLOCKED":
                # Already blocked — verification only
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RESTORE_BLOCKED", state="BLOCKED",
                    evidence_id=rs.proof_source_id,
                ))
            elif status == "RETAINED":
                # Backup is retained and blocked (no restore risk)
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RESTORE_BLOCKED", state="BLOCKED",
                    evidence_id=rs.proof_source_id,
                ))
            continue

        # --- RETAIN categories ---
        if action == "RETAIN":
            if status in ("RETAINED", "PRESENT", "ABSENT"):
                # Retained records should be present
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_PRESENT", state="PRESENT",
                    evidence_id=rs.proof_source_id,
                ))
            continue

        # --- DELETE action ---
        if action == "DELETE":
            if status in _NEEDS_DELETION or rs.was_recreated:
                # Finding
                evidence_id = rs.proof_source_id if not rs.is_claim else ""
                findings.append(Step(
                    step_no=0, phase="FINDING",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REPORT_REMAINING_RECORD", state="PRESENT",
                    evidence_id=evidence_id,
                ))
                # Remediation
                remediations.append(Step(
                    step_no=0, phase="REMEDIATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="DELETE_RECORD", state="ABSENT",
                    evidence_id="",
                ))
                # Verification
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ABSENT", state="ABSENT",
                    evidence_id="",
                ))
            elif status in _IS_ABSENT:
                # Already deleted — COMPLETE verification
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ABSENT", state="ABSENT",
                    evidence_id=rs.proof_source_id,
                ))
            # If RETAINED/ANONYMIZED/REDACTED, skip (shouldn't happen for DELETE)
            continue

        # --- REDACT action ---
        if action == "REDACT":
            if status in _NEEDS_REDACTION:
                evidence_id = rs.proof_source_id if not rs.is_claim else ""
                findings.append(Step(
                    step_no=0, phase="FINDING",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REPORT_EXPOSED_PII", state="PRESENT",
                    evidence_id=evidence_id,
                ))
                remediations.append(Step(
                    step_no=0, phase="REMEDIATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REDACT_RECORD", state="REDACTED",
                    evidence_id="",
                ))
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_REDACTED", state="REDACTED",
                    evidence_id="",
                ))
            elif status in _IS_REDACTED:
                # Already redacted — verification
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_REDACTED", state="REDACTED",
                    evidence_id=rs.proof_source_id,
                ))
            elif status in _IS_ABSENT:
                # Deleted instead of redacted — also acceptable, verify absent
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ABSENT", state="ABSENT",
                    evidence_id=rs.proof_source_id,
                ))
            continue

        # --- ANONYMIZE action ---
        if action == "ANONYMIZE":
            if status in _NEEDS_ANONYMIZATION:
                evidence_id = rs.proof_source_id if not rs.is_claim else ""
                findings.append(Step(
                    step_no=0, phase="FINDING",
                    system_id=rs.system_id, resource_id=rid,
                    operation="REPORT_EXPOSED_PII", state="PRESENT",
                    evidence_id=evidence_id,
                ))
                remediations.append(Step(
                    step_no=0, phase="REMEDIATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="ANONYMIZE_RECORD", state="ANONYMIZED",
                    evidence_id="",
                ))
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ANONYMIZED", state="ANONYMIZED",
                    evidence_id="",
                ))
            elif status in _IS_ANONYMIZED:
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ANONYMIZED", state="ANONYMIZED",
                    evidence_id=rs.proof_source_id,
                ))
            elif status in _IS_ABSENT:
                # Deleted instead of anonymized — verify absent
                verifications.append(Step(
                    step_no=0, phase="VERIFICATION",
                    system_id=rs.system_id, resource_id=rid,
                    operation="VERIFY_RECORD_ABSENT", state="ABSENT",
                    evidence_id=rs.proof_source_id,
                ))
            continue

    is_complete = len(findings) == 0 and len(remediations) == 0

    return findings, remediations, verifications, is_complete


def build_step_list(
    states: Dict[str, ResourceState],
    policy: Dict[str, str],
    deletion_status: str,
    is_shared_support: Optional[callable] = None,
) -> List[Step]:
    """
    Build final ordered, numbered step list.

    For COMPLETE: verification steps only (with evidence IDs).
    For INCOMPLETE: finding + remediation + verification steps.
    For NOT_APPLICABLE: [].
    """
    if deletion_status == "NOT_APPLICABLE":
        return []

    findings, remediations, verifications, is_complete = plan_steps(
        states, policy, is_shared_support
    )

    if is_complete:
        # COMPLETE: only verification steps with real evidence IDs
        all_steps = [s for s in verifications if s.evidence_id]
        if not all_steps:
            # No evidence-backed verifications found — treat as truly complete with no steps
            all_steps = verifications
    else:
        # INCOMPLETE: all three phases
        all_steps = findings + remediations + verifications

    all_steps = _sort_steps(all_steps)

    # Number steps from 1
    for i, step in enumerate(all_steps, 1):
        step.step_no = i

    return all_steps
