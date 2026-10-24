"""
State reconstruction: given an IdentitySet and audit_at, determines the
"true" state of every relevant resource at audit_at.

Algorithm per resource_id R:
1. Gather all observations with R in their identifiers (via ObservationStore).
2. Filter to observed_at <= audit_at.
3. Sort by observed_at ascending (stable).
4. Apply precedence:
   - Non-claim observations override claims.
   - Latest non-claim observation's status is authoritative.
   - If only claims exist, use the latest claim.
5. Detect post-deletion recreation:
   - If evidence shows ABSENT at time T1 then PRESENT at T2 > T1 (non-claim), the record was recreated.
6. Tag backup entries as RESTORABLE if restore_allowed=True in any non-claim observation.
7. Tag data flows as ACTIVE if enabled=True in the latest non-claim observation.

Returns a dict {resource_id: ResourceState}
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from audit.models import Observation
from audit.store import ObservationStore


@dataclass
class ResourceState:
    """Reconstructed state of one resource at audit_at."""
    resource_id: str
    system_id: str
    record_type: Optional[str]
    status: str                        # Authoritative status: PRESENT, ABSENT, REDACTED, ANONYMIZED, ACTIVE, DISABLED, RESTORABLE, BLOCKED, RETAINED
    proof_source_id: str               # file_id / activity_id of authoritative evidence
    proof_observed_at: datetime
    identifiers: FrozenSet[str]       # Union of all matching identifiers seen
    was_recreated: bool = False        # True if evidence shows recreation post-deletion
    is_claim: bool = False             # True only if no non-claim evidence at all


# Status rank: higher = more "present" — used to break ties when timestamps are equal
_STATUS_PRESENCE_RANK = {
    "PRESENT": 10,
    "EXPOSED": 10,
    "ACTIVE": 9,
    "RESTORABLE": 8,
    "REDACTED": 5,
    "ANONYMIZED": 4,
    "RETAINED": 3,
    "DISABLED": 2,
    "BLOCKED": 2,
    "ABSENT": 0,
}

# Statuses that mean the record is effectively gone
_ABSENT_STATUSES = {"ABSENT"}


def _authoritative_status(observations: List[Observation]) -> tuple:
    """
    Pick the authoritative status from a list of observations for one resource.

    Returns (status, source_id, observed_at, is_claim).
    """
    if not observations:
        return ("ABSENT", "", datetime.min.replace(tzinfo=timezone.utc), True)

    non_claims = [o for o in observations if not o.is_claim]
    claims = [o for o in observations if o.is_claim]

    if non_claims:
        # Latest non-claim wins
        best = max(non_claims, key=lambda o: (o.observed_at, _STATUS_PRESENCE_RANK.get(o.status, 0)))
        return (best.status, best.source_id, best.observed_at, False)
    else:
        # Only claims available
        best = max(claims, key=lambda o: (o.observed_at, _STATUS_PRESENCE_RANK.get(o.status, 0)))
        return (best.status, best.source_id, best.observed_at, True)


def _detect_recreation(observations: List[Observation]) -> bool:
    """
    Detect if a record was recreated after deletion.

    Pattern: ABSENT at T1 (non-claim) followed by PRESENT at T2 > T1 (non-claim).
    """
    non_claims = sorted(
        [o for o in observations if not o.is_claim],
        key=lambda o: o.observed_at,
    )
    last_absent_at: Optional[datetime] = None
    for obs in non_claims:
        if obs.status in _ABSENT_STATUSES:
            last_absent_at = obs.observed_at
        elif obs.status == "PRESENT" and last_absent_at is not None:
            if obs.observed_at > last_absent_at:
                return True
    return False


def _pick_system(observations: List[Observation], resource_id: str) -> str:
    """Pick the best system_hint for a resource."""
    from config import PREFIX_SYSTEM_CATEGORY
    # Try prefix map first
    for prefix, (sys_name, _) in PREFIX_SYSTEM_CATEGORY.items():
        if resource_id.startswith(prefix.rstrip("_") + "_"):
            return sys_name
    # Fall back to most common non-empty hint
    hints = [o.system_hint for o in observations if o.system_hint and o.system_hint != "unknown_service"]
    if hints:
        from collections import Counter
        return Counter(hints).most_common(1)[0][0]
    hints_any = [o.system_hint for o in observations if o.system_hint]
    if hints_any:
        from collections import Counter
        return Counter(hints_any).most_common(1)[0][0]
    return "unknown_service"


def _pick_record_type(observations: List[Observation]) -> Optional[str]:
    """Pick the most common non-None record_type."""
    types = [o.record_type for o in observations if o.record_type]
    if not types:
        return None
    from collections import Counter
    return Counter(types).most_common(1)[0][0]


def _union_identifiers(observations: List[Observation]) -> FrozenSet[str]:
    result: Set[str] = set()
    for o in observations:
        result.update(o.identifiers)
    return frozenset(result)


def reconstruct_state(
    identity_ids: FrozenSet[str],
    audit_at: datetime,
    store: ObservationStore,
    extra_resource_ids: Optional[Set[str]] = None,
) -> Dict[str, ResourceState]:
    """
    Reconstruct the state of every resource linked to the subject at audit_at.

    Args:
        identity_ids: all normalized identifiers for the subject
        audit_at: cutoff timestamp
        store: loaded ObservationStore
        extra_resource_ids: optional additional resource IDs to include

    Returns:
        dict mapping resource_id -> ResourceState
    """
    # Gather all relevant observations matching identity identifiers at or before audit_at
    candidate_obs = store.get_for_identifiers(identity_ids, up_to=audit_at)
    
    # Enforce strict citable_at <= audit_at (no future evidence files)
    valid_matching_obs = [
        o for o in candidate_obs
        if o.citable_at <= audit_at and o.observed_at <= audit_at
    ]

    # Collect all relevant resource IDs
    relevant_rids = set()
    for obs in valid_matching_obs:
        if obs.resource_id:
            relevant_rids.add(obs.resource_id)

    if extra_resource_ids:
        relevant_rids.update(extra_resource_ids)

    # For every relevant resource, pull ALL its observations up to audit_at
    # (including observations that no longer carry direct identifiers, such as 404 readbacks or redacted rows)
    by_resource: Dict[str, List[Observation]] = {}
    for rid in relevant_rids:
        all_rid_obs = store.get_for_resource(rid, up_to=audit_at)
        valid_rid_obs = [
            o for o in all_rid_obs
            if o.citable_at <= audit_at and o.observed_at <= audit_at
        ]
        if valid_rid_obs:
            by_resource[rid] = valid_rid_obs

    states: Dict[str, ResourceState] = {}
    for rid, obs_list in by_resource.items():
        # Skip purely identity/audit-trail records with no resource_id purpose
        if not any(o.record_type not in ("USER_IDENTITY", "IDENTITY_AUDIT") for o in obs_list):
            continue

        status, source_id, observed_at, is_claim = _authoritative_status(obs_list)
        was_recreated = _detect_recreation(obs_list)
        system_id = _pick_system(obs_list, rid)
        record_type = _pick_record_type(obs_list)
        idents = _union_identifiers(obs_list)

        states[rid] = ResourceState(
            resource_id=rid,
            system_id=system_id,
            record_type=record_type,
            status=status,
            proof_source_id=source_id,
            proof_observed_at=observed_at,
            identifiers=idents,
            was_recreated=was_recreated,
            is_claim=is_claim,
        )

    return states
