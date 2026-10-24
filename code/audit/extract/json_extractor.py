import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..config import PREFIX_SYSTEM_CATEGORY
from ..loaders import norm_email, norm_name, norm_phone, parse_iso_ts
from ..models import EvidenceFile, Observation

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
SHA256_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")
USER_ID_REGEX = re.compile(r"^user_\d+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s()-]{7,25}$")

def map_raw_status(d: Dict[str, Any], record_type: Optional[str] = None) -> str:
    """Map raw status/result/enabled/restore_allowed fields to canonical status."""
    # 0. Check status_code / absence markers
    if d.get("status_code") in (404, "404") or (d.get("profile") is None and "profile" in d):
        return "ABSENT"

    # 1. enabled / restore_allowed
    if "enabled" in d:
        val = d["enabled"]
        return "ACTIVE" if val in (True, 1, "true", "1") else "DISABLED"
    if "restore_allowed" in d:
        val = d["restore_allowed"]
        return "RESTORABLE" if val in (True, 1, "true", "1") else "BLOCKED"

    # 2. Check result, status, state, account_status
    raw_status = None
    for k in ["result", "status", "state", "account_status", "delivery_status"]:
        if k in d and d[k] is not None:
            raw_status = str(d[k]).strip().upper()
            break

    if raw_status:
        if raw_status in ("NOT_FOUND", "ABSENT", "NOT_PRESENT"):
            return "ABSENT"
        if raw_status in ("FOUND", "PRESENT", "IDENTIFIABLE", "EXPOSED"):
            return "PRESENT"
        if raw_status in ("ANONYMIZED", "ANONYMOUS"):
            return "ANONYMIZED"
        if raw_status in ("REDACTED", "CLEAN"):
            return "REDACTED"
        if raw_status in ("ACTIVE", "ENABLED"):
            return "ACTIVE"
        if raw_status in ("DISABLED", "INACTIVE"):
            return "DISABLED"
        if raw_status in ("BLOCKED", "RESTORE_BLOCKED"):
            return "BLOCKED"
        if raw_status in ("RESTORABLE", "RESTORE_ALLOWED"):
            return "RESTORABLE"
        if raw_status in ("RETAINED", "RETAIN"):
            return "RETAINED"
        if raw_status in ("DELETED",):
            # Check if this is a tombstone record with PII still present
            pii_cols = ["name", "email", "phone", "email_hash", "full_name"]
            has_tombstone_pii = any(d.get(col) is not None and str(d.get(col)).strip() != "" for col in pii_cols)
            if has_tombstone_pii:
                return "PRESENT"
            elif any(d.get(c) for c in ["subject_reference", "user_id", "customer_reference"]):
                return "REDACTED"
            return "ABSENT"

    # 3. Check PII nullness for records without an explicit status field
    # E.g. in service_resource_export, fields with None values
    pii_keys = [
        "email", "phone", "name", "full_name", "display_name",
        "requester_email", "requester_phone", "requester_name",
        "owner_email", "owner_phone", "customer_email",
    ]
    ref_keys = ["user_id", "customer_reference", "subject_reference"]

    has_pii = any(d.get(k) is not None and str(d.get(k)).strip() != "" for k in pii_keys)
    has_ref = any(d.get(k) is not None and str(d.get(k)).strip() != "" for k in ref_keys)

    # If any PII key was explicitly present in dictionary (even if None)
    has_pii_schema = any(k in d for k in pii_keys)
    if has_pii_schema:
        if has_pii:
            return "PRESENT"
        elif has_ref:
            return "REDACTED"
        else:
            return "ANONYMIZED"

    return "PRESENT"

def extract_identifiers_from_dict(d: Dict[str, Any]) -> Set[str]:
    """Recursively extract emails, hashes, user_ids, phones from any dictionary."""
    idents: Set[str] = set()
    for k, v in d.items():
        if isinstance(v, str):
            val = v.strip()
            if not val:
                continue
            lower_k = k.lower()
            if "user_id" in lower_k or "customer_reference" in lower_k or "subject_reference" in lower_k:
                idents.add(val)
            elif "hash" in lower_k and SHA256_REGEX.match(val):
                idents.add(val.lower())
            elif "email" in lower_k and EMAIL_REGEX.match(val):
                idents.add(norm_email(val))
            elif "phone" in lower_k and PHONE_REGEX.match(val):
                idents.add(norm_phone(val))
            elif USER_ID_REGEX.match(val):
                idents.add(val)
            elif SHA256_REGEX.match(val):
                idents.add(val.lower())
            elif EMAIL_REGEX.match(val):
                idents.add(norm_email(val))
        elif isinstance(v, dict):
            idents.update(extract_identifiers_from_dict(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    idents.update(extract_identifiers_from_dict(item))
                elif isinstance(item, str):
                    val = item.strip()
                    if EMAIL_REGEX.match(val):
                        idents.add(norm_email(val))
                    elif USER_ID_REGEX.match(val):
                        idents.add(val)
                    elif SHA256_REGEX.match(val):
                        idents.add(val.lower())
    return idents

def extract_json_evidence(
    json_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Recursively walk JSON evidence files and emit Observations."""
    observations: List[Observation] = []
    source_id = evidence_file.file_id if evidence_file else json_path.stem
    manifest_citable_at = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def walk(node: Any, current_ts: datetime, current_system: Optional[str], path_str: str):
        if isinstance(node, dict):
            # Check for timestamps at this level
            level_ts = current_ts
            for ts_key in ["captured_at", "recorded_at", "exported_at", "updated_at", "timestamp", "event_time"]:
                if ts_key in node and node[ts_key]:
                    parsed = parse_iso_ts(node[ts_key])
                    if parsed > datetime.min.replace(tzinfo=timezone.utc):
                        level_ts = parsed
                        break

            # Check for system/service hints at this level
            level_system = current_system
            for sys_key in ["system", "data_store", "source", "origin", "service"]:
                if sys_key in node and node[sys_key]:
                    val = str(node[sys_key]).strip()
                    if val:
                        level_system = val
                        break

            # If node represents a resource record
            rid = None
            for id_key in ["resource_id", "record_id", "ticket_id", "id"]:
                if id_key in node and node[id_key]:
                    val = str(node[id_key]).strip()
                    if val:
                        rid = val
                        break

            if rid:
                record_type = node.get("record_type") or node.get("type") or node.get("collection")
                
                # Derive system and record_type from prefix if not provided
                system_id = level_system
                if not record_type or not system_id:
                    for prefix, (default_sys, default_cat) in PREFIX_SYSTEM_CATEGORY.items():
                        if rid.startswith(prefix):
                            if not system_id:
                                system_id = default_sys
                            if not record_type:
                                record_type = default_cat
                            break

                # Extract status
                status = map_raw_status(node, record_type)

                # Extract identifiers from node and nested objects (like document)
                idents = extract_identifiers_from_dict(node)

                obs = Observation(
                    source_id=source_id,
                    source_kind="file",
                    observed_at=level_ts,
                    citable_at=manifest_citable_at,
                    system_hint=system_id,
                    resource_id=rid,
                    record_type=str(record_type) if record_type else None,
                    status=status,
                    identifiers=frozenset(idents),
                    fields=dict(node),
                    is_claim=False,
                    raw_ref=f"{json_path.name}:{path_str}",
                )
                observations.append(obs)

            # Recurse children
            for k, v in node.items():
                if k != "document": # don't double emit if document is just payload
                    walk(v, level_ts, level_system, f"{path_str}.{k}")

        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, current_ts, current_system, f"{path_str}[{idx}]")

    walk(data, manifest_citable_at, None, "$")
    return observations
