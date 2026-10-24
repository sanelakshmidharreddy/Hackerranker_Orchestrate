from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, FrozenSet, List, Optional, Set

@dataclass(frozen=True)
class Observation:
    source_id: str          # file_id (evidence_NN) or activity_id or audit_id
    source_kind: str        # 'file' | 'activity' | 'audit'
    observed_at: datetime   # most specific timestamp available (UTC)
    citable_at: datetime    # manifest captured_at for files; event_time otherwise
    system_hint: Optional[str]   # data_store / service / table-derived system
    resource_id: Optional[str]
    record_type: Optional[str]   # USER_PROFILE, SEARCH_INDEX_ENTRY, etc.
    status: str             # PRESENT | ABSENT | REDACTED | ANONYMIZED | ACTIVE | DISABLED | BLOCKED | RESTORABLE | RETAINED | UNKNOWN
    identifiers: FrozenSet[str]  # normalized emails, hashes, phones, names, user_ids
    fields: Dict[str, Any]       # raw fields (which PII columns are non-null, etc.)
    is_claim: bool          # True for workflow/activity claims, submissions
    raw_ref: str            # file path + line/row/json-path for debugging

@dataclass(frozen=True)
class Case:
    case_id: str
    email: str
    requested_at: datetime
    reported_status: str
    reported_at: datetime
    audit_at: datetime
    request_text: str

@dataclass
class Identity:
    user_id: str
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    hashes: Set[str] = field(default_factory=set)
    names: Set[str] = field(default_factory=set)
    linked_resource_ids: Set[str] = field(default_factory=set)
    provenance: Dict[str, str] = field(default_factory=dict)

    def all_identifiers(self) -> Set[str]:
        return {self.user_id} | self.emails | self.phones | self.hashes | self.names

@dataclass(frozen=True)
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_no": self.step_no,
            "phase": self.phase,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "state": self.state,
            "evidence_id": self.evidence_id,
        }

@dataclass(frozen=True)
class DeletionRule:
    rule_id: str
    data_category: str
    condition: str
    required_action: str

@dataclass(frozen=True)
class EvidenceFile:
    file_id: str
    file_path: str
    origin: str
    captured_at: datetime

@dataclass(frozen=True)
class UserIdentityRow:
    user_id: str
    name: str
    email: str
    phone: str
    email_hash: str
    updated_at: datetime

@dataclass(frozen=True)
class UserAuditLogRow:
    audit_id: str
    user_id: str
    event_time: datetime
    field_name: str
    old_value: str
    new_value: str

@dataclass(frozen=True)
class SystemActivityRow:
    activity_id: str
    event_time: datetime
    event_type: str
    source_system: str
    target_system: str
    resource_id: str
    reported_result: str
    details: str
