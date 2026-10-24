from datetime import timezone
from typing import List

from ..loaders import email_hash, norm_email, norm_name, norm_phone
from ..models import Observation, UserAuditLogRow, UserIdentityRow

def extract_user_audit_observations(
    audit_rows: List[UserAuditLogRow],
) -> List[Observation]:
    """Convert user_audit_log.csv rows to Observation objects with source_kind='audit'."""
    observations: List[Observation] = []
    for r in audit_rows:
        idents = {r.user_id}
        norm_old = r.old_value.strip()
        norm_new = r.new_value.strip()

        if r.field_name == "email":
            norm_old = norm_email(norm_old)
            norm_new = norm_email(norm_new)
            idents.add(norm_old)
            idents.add(norm_new)
            idents.add(email_hash(norm_old))
            idents.add(email_hash(norm_new))
        elif r.field_name == "email_hash":
            idents.add(norm_old.lower())
            idents.add(norm_new.lower())
        elif r.field_name == "phone":
            norm_old = norm_phone(norm_old)
            norm_new = norm_phone(norm_new)
            idents.add(norm_old)
            idents.add(norm_new)

        obs = Observation(
            source_id=r.audit_id,
            source_kind="audit",
            observed_at=r.event_time,
            citable_at=r.event_time,
            system_hint="identity_service",
            resource_id=None,
            record_type="IDENTITY_AUDIT",
            status="RETAINED",
            identifiers=frozenset(idents),
            fields={
                "field_name": r.field_name,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "user_id": r.user_id,
            },
            is_claim=False,
            raw_ref=f"user_audit_log.csv:{r.audit_id}",
        )
        observations.append(obs)
    return observations

def extract_user_identity_observations(
    identities: List[UserIdentityRow],
) -> List[Observation]:
    """Convert user_identities.csv rows to Observation objects with source_kind='identity'."""
    observations: List[Observation] = []
    for u in identities:
        idents = {
            u.user_id,
            norm_email(u.email),
            norm_phone(u.phone),
            u.email_hash.strip().lower(),
            norm_name(u.name),
        }
        obs = Observation(
            source_id=u.user_id,
            source_kind="identity",
            observed_at=u.updated_at,
            citable_at=u.updated_at,
            system_hint="identity_service",
            resource_id=None,
            record_type="USER_IDENTITY",
            status="PRESENT",
            identifiers=frozenset(idents),
            fields={
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "email_hash": u.email_hash,
            },
            is_claim=False,
            raw_ref=f"user_identities.csv:{u.user_id}",
        )
        observations.append(obs)
    return observations
