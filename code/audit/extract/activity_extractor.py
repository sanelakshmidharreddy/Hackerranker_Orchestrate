import re
from typing import Dict, List, Set

from ..config import PREFIX_SYSTEM_CATEGORY
from ..loaders import norm_email, parse_iso_ts
from ..models import Observation, SystemActivityRow

EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
USER_ID_REGEX = re.compile(r"(user_\d+)")
RESOURCE_ID_REGEX = re.compile(r"([a-zA-Z]+_\d+)")

def extract_activity_observations(
    activities: List[SystemActivityRow],
) -> List[Observation]:
    """Convert system_activity.csv rows to Observation objects with claim vs proof distinction."""
    observations: List[Observation] = []

    for row in activities:
        ev_type = row.event_type
        res = row.reported_result
        details = row.details
        rid = row.resource_id
        target_sys = row.target_system
        obs_ts = row.event_time

        # Extract identifiers from details and rid
        idents: Set[str] = set()
        for em in EMAIL_REGEX.findall(details):
            idents.add(norm_email(em))
        for uid in USER_ID_REGEX.findall(details):
            idents.add(uid)

        # Map target system and category
        system_id = target_sys
        record_type = None
        for prefix, (default_sys, default_cat) in PREFIX_SYSTEM_CATEGORY.items():
            if rid.startswith(prefix):
                system_id = default_sys
                record_type = default_cat
                break

        # Distinguish Claims vs Inspections vs Recreations
        is_claim = True
        status = "UNKNOWN"

        lower_details = details.lower()

        if ev_type in ("DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD", "DISABLE_DATA_FLOW", "BLOCK_RESTORE"):
            is_claim = True
            if ev_type == "DELETE_RECORD":
                status = "CLAIM_ABSENT" if res == "SUCCESS" else "CLAIM_FAILED"
            elif ev_type == "REDACT_RECORD":
                status = "CLAIM_REDACTED" if res == "SUCCESS" else "CLAIM_FAILED"
            elif ev_type == "ANONYMIZE_RECORD":
                status = "CLAIM_ANONYMIZED" if res == "SUCCESS" else "CLAIM_FAILED"
            elif ev_type == "DISABLE_DATA_FLOW":
                status = "CLAIM_DISABLED" if res == "SUCCESS" else "CLAIM_FAILED"
            elif ev_type == "BLOCK_RESTORE":
                status = "CLAIM_BLOCKED" if res == "SUCCESS" else "CLAIM_FAILED"

        elif ev_type == "CHECK_DATA_FLOW":
            is_claim = False # Inspection check
            if "remains enabled" in lower_details or "enabled" in lower_details:
                status = "ACTIVE"
            else:
                status = "DISABLED"

        elif ev_type == "CHECK_RESTORE_ACCESS":
            is_claim = False # Inspection check
            if "can still be restored" in lower_details or "restorable" in lower_details:
                status = "RESTORABLE"
            else:
                status = "BLOCKED"

        elif ev_type in ("SYNC_RECORD", "INDEX_RECORD", "UPDATE_RECORD", "RESTORE_BACKUP", "CREATE_EXPORT"):
            # Strong recreation / writing signal
            is_claim = False
            status = "PRESENT"

        elif ev_type == "LINK_RESOURCE_IDENTITY":
            is_claim = False
            status = "PRESENT"

        elif ev_type == "CLASSIFY_REQUEST":
            is_claim = False
            status = "NON_DELETION"

        elif ev_type == "RETAIN_RECORD":
            is_claim = False
            status = "RETAINED"

        obs = Observation(
            source_id=row.activity_id,
            source_kind="activity",
            observed_at=obs_ts,
            citable_at=obs_ts,
            system_hint=system_id,
            resource_id=rid if rid else None,
            record_type=record_type,
            status=status,
            identifiers=frozenset(idents),
            fields={
                "event_type": ev_type,
                "reported_result": res,
                "details": details,
                "source_system": row.source_system,
                "target_system": target_sys,
            },
            is_claim=is_claim,
            raw_ref=f"system_activity.csv:{row.activity_id}",
        )
        observations.append(obs)

    return observations
