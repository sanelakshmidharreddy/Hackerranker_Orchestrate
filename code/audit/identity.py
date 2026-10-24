"""
Identity resolver: given a case email (current or historical), builds the
complete set S of identifiers for the subject.

Identity set S is built from:
1. user_identities.csv — current snapshot (any row whose email or email_hash matches)
2. user_audit_log.csv  — historical values (old_value/new_value for field email/phone/email_hash)
   filtered to events at or before audit_at
3. Derived: sha256(norm(email)) for every email found

Matching is always exact-normalized (no fuzzy, no name matching).
"""

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from audit.loaders import email_hash, norm_email, norm_phone


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class IdentitySet:
    """Resolved identity for a single data subject."""

    def __init__(self):
        self.user_ids: Set[str] = set()          # user_NNN
        self.emails: Set[str] = set()             # normalized emails
        self.phones: Set[str] = set()             # normalized phones
        self.email_hashes: Set[str] = set()       # sha256 lowercase hexstrings

    @property
    def all_identifiers(self) -> frozenset:
        return frozenset(
            self.user_ids | self.emails | self.phones | self.email_hashes
        )

    def add_email(self, e: str) -> None:
        if not e:
            return
        ne = norm_email(e)
        if ne:
            self.emails.add(ne)
            self.email_hashes.add(email_hash(ne))

    def add_phone(self, p: str) -> None:
        if not p:
            return
        np = norm_phone(p)
        if np:
            self.phones.add(np)

    def add_user_id(self, uid: str) -> None:
        if uid and uid.startswith("user_"):
            self.user_ids.add(uid)

    def __repr__(self):
        return (
            f"IdentitySet(user_ids={self.user_ids}, emails={self.emails}, "
            f"phones={self.phones}, hashes={len(self.email_hashes)} hashes)"
        )


def resolve_identity(
    case_email: str,
    audit_at: datetime,
    identity_rows,
    audit_log_rows,
) -> IdentitySet:
    """
    Build the complete identity set S for the subject identified by case_email,
    considering only evidence at or before audit_at.

    Args:
        case_email: the email from deletion_requests.csv (may be historical)
        audit_at: cutoff datetime
        identity_rows: list of UserIdentityRow from user_identities.csv
        audit_log_rows: list of UserAuditLogRow from user_audit_log.csv

    Returns:
        IdentitySet with all confirmed identifiers for the subject.
    """
    identity = IdentitySet()
    ne_case = norm_email(case_email)
    case_hash = email_hash(ne_case) if ne_case else ""

    # Step 1: Find the user_id via current snapshot
    matched_user_id: Optional[str] = None
    for row in identity_rows:
        ne_row = norm_email(row.email)
        row_hash = row.email_hash.strip().lower()
        if ne_row == ne_case or (case_hash and row_hash == case_hash):
            matched_user_id = row.user_id
            identity.add_user_id(row.user_id)
            identity.add_email(row.email)
            identity.add_phone(row.phone)
            identity.email_hashes.add(row_hash)
            break

    # Step 2: If not found by current email, search audit log for historical email
    if not matched_user_id:
        for row in audit_log_rows:
            if row.event_time > audit_at:
                continue
            if row.field_name != "email":
                continue
            ne_old = norm_email(row.old_value)
            ne_new = norm_email(row.new_value)
            if ne_old == ne_case or ne_new == ne_case:
                matched_user_id = row.user_id
                identity.add_user_id(row.user_id)
                identity.add_email(row.old_value)
                identity.add_email(row.new_value)
                break

        # If found via audit, also load the current snapshot for that user
        if matched_user_id:
            for row in identity_rows:
                if row.user_id == matched_user_id:
                    identity.add_email(row.email)
                    identity.add_phone(row.phone)
                    identity.email_hashes.add(row.email_hash.strip().lower())
                    break

    if not matched_user_id:
        # Fallback: use the case email only
        identity.add_email(case_email)
        return identity

    # Step 3: Expand from all audit log events for this user at or before audit_at
    for row in audit_log_rows:
        if row.user_id != matched_user_id:
            continue
        if row.event_time > audit_at:
            continue
        if row.field_name == "email":
            identity.add_email(row.old_value)
            identity.add_email(row.new_value)
        elif row.field_name == "email_hash":
            old_h = row.old_value.strip().lower()
            new_h = row.new_value.strip().lower()
            if old_h:
                identity.email_hashes.add(old_h)
            if new_h:
                identity.email_hashes.add(new_h)
        elif row.field_name == "phone":
            identity.add_phone(row.old_value)
            identity.add_phone(row.new_value)

    return identity
