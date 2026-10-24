import csv
import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

from .models import (
    Case,
    DeletionRule,
    EvidenceFile,
    SystemActivityRow,
    UserAuditLogRow,
    UserIdentityRow,
)

# --- Normalization Helpers (Section 6.1) ---

def norm_email(s: Optional[str]) -> str:
    """Normalize email: strip whitespace, lowercase.
    Preserves dots and plus tags to distinguish decoys."""
    if not s:
        return ""
    return s.strip().lower()

def norm_phone(s: Optional[str]) -> str:
    """Normalize phone: keep leading + and digits only."""
    if not s:
        return ""
    s = s.strip()
    has_plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    return f"+{digits}" if has_plus else digits

def norm_name(s: Optional[str]) -> str:
    """Normalize name: Unicode NFKC, casefold, collapse whitespace.
    Names are weak identifiers; never match on a name alone."""
    if not s:
        return ""
    normalized = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"\s+", " ", normalized).strip()

def email_hash(e: Optional[str]) -> str:
    """Compute SHA-256 hash of normalized email."""
    if not e:
        return ""
    return hashlib.sha256(norm_email(e).encode("utf-8")).hexdigest()

def parse_iso_ts(ts_str: Optional[str]) -> datetime:
    """Parse ISO-8601 timestamp string into timezone-aware UTC datetime."""
    if not ts_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    s = ts_str.strip()
    # Normalize Z to +00:00 for fromisoformat
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        # Fallback format parsing
        for fmt in [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                dt = datetime.strptime(s, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except Exception:
                continue
    return datetime.min.replace(tzinfo=timezone.utc)

def case_sort_key(cid: str) -> int:
    """Natural numeric sort key for case IDs (e.g. 'case_33' -> 33)."""
    try:
        return int(cid.split("_", 1)[1])
    except Exception:
        return 0

# --- CSV Loaders ---

def load_deletion_requests(path: Union[str, Path]) -> List[Case]:
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(
                Case(
                    case_id=row["case_id"].strip(),
                    email=norm_email(row["email"]),
                    requested_at=parse_iso_ts(row["requested_at"]),
                    reported_status=row["reported_status"].strip(),
                    reported_at=parse_iso_ts(row["reported_at"]),
                    audit_at=parse_iso_ts(row["audit_at"]),
                    request_text=row["request_text"].strip(),
                )
            )
    return cases

def load_user_identities(path: Union[str, Path]) -> List[UserIdentityRow]:
    identities = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            identities.append(
                UserIdentityRow(
                    user_id=row["user_id"].strip(),
                    name=row["name"].strip(),
                    email=norm_email(row["email"]),
                    phone=norm_phone(row["phone"]),
                    email_hash=row["email_hash"].strip(),
                    updated_at=parse_iso_ts(row["updated_at"]),
                )
            )
    return identities

def load_user_audit_log(path: Union[str, Path]) -> List[UserAuditLogRow]:
    audit_rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audit_rows.append(
                UserAuditLogRow(
                    audit_id=row["audit_id"].strip(),
                    user_id=row["user_id"].strip(),
                    event_time=parse_iso_ts(row["event_time"]),
                    field_name=row["field_name"].strip(),
                    old_value=row["old_value"].strip(),
                    new_value=row["new_value"].strip(),
                )
            )
    return audit_rows

def load_deletion_rules(path: Union[str, Path]) -> List[DeletionRule]:
    rules = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = row.get("rule_id") or row.get("rule") or ""
            rules.append(
                DeletionRule(
                    rule_id=rid.strip(),
                    data_category=row["data_category"].strip(),
                    condition=row["condition"].strip(),
                    required_action=row["required_action"].strip(),
                )
            )
    return rules

def load_evidence_manifest(path: Union[str, Path]) -> Dict[str, EvidenceFile]:
    manifest = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = row["file_id"].strip()
            manifest[fid] = EvidenceFile(
                file_id=fid,
                file_path=row["file_path"].strip(),
                origin=row["origin"].strip(),
                captured_at=parse_iso_ts(row["captured_at"]),
            )
    return manifest

def load_system_activity(path: Union[str, Path]) -> List[SystemActivityRow]:
    activities = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            activities.append(
                SystemActivityRow(
                    activity_id=row["activity_id"].strip(),
                    event_time=parse_iso_ts(row["event_time"]),
                    event_type=row["event_type"].strip(),
                    source_system=row["source_system"].strip(),
                    target_system=row["target_system"].strip(),
                    resource_id=row["resource_id"].strip(),
                    reported_result=row["reported_result"].strip(),
                    details=row["details"].strip(),
                )
            )
    return activities
