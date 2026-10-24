import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..loaders import norm_email, norm_name, norm_phone, parse_iso_ts
from ..models import EvidenceFile, Observation

def extract_sql_evidence(
    sql_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Extract Observations from an SQLite-compatible SQL snapshot file."""
    observations: List[Observation] = []
    text = sql_path.read_text(encoding="utf-8")
    source_id = evidence_file.file_id if evidence_file else sql_path.stem

    # Extract manifest citable timestamp
    manifest_citable_at = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    # 1. Parse header comments for captured_at and topology
    header_captured_at = None
    header_cap_match = re.search(r"--\s*Captured at:\s*(\S+)", text)
    if header_cap_match:
        header_captured_at = parse_iso_ts(header_cap_match.group(1))

    # 2. Parse trailer -- snapshot_completed_at=
    trailer_captured_at = None
    trailer_match = re.search(r"--\s*snapshot_completed_at=(\S+)", text)
    if trailer_match:
        trailer_captured_at = parse_iso_ts(trailer_match.group(1))

    # Connect to in-memory sqlite
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(text)
        cur = conn.cursor()

        # Check snapshot_scope table
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshot_scope';")
        has_scope = cur.fetchone() is not None
        scope_system = None
        scope_captured_at = None
        if has_scope:
            cur.execute("SELECT origin_system, captured_at FROM snapshot_scope LIMIT 1;")
            row = cur.fetchone()
            if row:
                scope_system = row[0]
                scope_captured_at = parse_iso_ts(row[1])

        # Priority of file-level timestamp:
        # scope_captured_at > trailer_captured_at > header_captured_at > manifest_citable_at
        file_ts = (
            scope_captured_at
            or trailer_captured_at
            or header_captured_at
            or manifest_citable_at
        )

        # Get all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall() if r[0] != "snapshot_scope"]

        for tbl in tables:
            # Map table name to category and system
            lower_tbl = tbl.lower()
            record_type = None
            system_id = None
            replica_role = "primary"
            if "failover" in lower_tbl or "replica" in lower_tbl:
                replica_role = "replica"
            elif "primary" in lower_tbl:
                replica_role = "primary"

            if "customer_profiles" in lower_tbl:
                record_type = "USER_PROFILE"
                system_id = "account_service"
            elif "customer_search_documents" in lower_tbl:
                record_type = "SEARCH_INDEX_ENTRY"
                system_id = "search_service"
            elif "customer_analytics_profiles" in lower_tbl:
                record_type = "ANALYTICS_PROFILE"
                system_id = "analytics_platform"
            elif "support_records" in lower_tbl:
                record_type = "SUPPORT_MESSAGE"
                system_id = "support_platform"
            elif "customer_exports" in lower_tbl:
                record_type = "USER_EXPORT"
                system_id = "export_service"
            elif "connector_subscriptions" in lower_tbl:
                record_type = "DATA_FLOW"
                system_id = "integration_service"
            elif "backup_restore_entries" in lower_tbl:
                record_type = "BACKUP_ARCHIVE"
                system_id = "backup_service"
            elif "security_audit_records" in lower_tbl:
                record_type = "SECURITY_AUDIT_LOG"
                system_id = "security_service"
            else:
                record_type = "UNKNOWN"
                system_id = scope_system or "unknown_service"

            # Fetch columns
            cur.execute(f"PRAGMA table_info({tbl});")
            col_info = cur.fetchall()
            col_names = [c[1] for c in col_info]

            cur.execute(f"SELECT * FROM {tbl};")
            rows = cur.fetchall()

            for row_idx, r in enumerate(rows):
                row_dict = dict(zip(col_names, r))
                
                # Check for nested JSON columns (e.g. record_json, payload, data)
                for json_col in ["record_json", "payload", "data"]:
                    raw_json = row_dict.get(json_col)
                    if raw_json and isinstance(raw_json, str):
                        try:
                            parsed_json = json.loads(raw_json)
                            if isinstance(parsed_json, dict):
                                # If document is nested (e.g. search documents)
                                if "document" in parsed_json and isinstance(parsed_json["document"], dict):
                                    for dk, dv in parsed_json["document"].items():
                                        if dk not in parsed_json:
                                            parsed_json[dk] = dv
                                for jk, jv in parsed_json.items():
                                    if jk not in row_dict or row_dict[jk] is None:
                                        row_dict[jk] = jv
                        except Exception:
                            pass

                # Derive record_type and system_id from collection_name / origin_system if UNKNOWN
                col_name_val = str(row_dict.get("collection_name", "")).lower()
                origin_sys_val = str(row_dict.get("origin_system", "")).strip()
                if origin_sys_val:
                    system_id = origin_sys_val

                if "customer_profile" in col_name_val:
                    record_type = "USER_PROFILE"
                    if not origin_sys_val:
                        system_id = "account_service"
                elif "search" in col_name_val:
                    record_type = "SEARCH_INDEX_ENTRY"
                    if not origin_sys_val:
                        system_id = "search_service"
                elif "analytics" in col_name_val:
                    record_type = "ANALYTICS_PROFILE"
                    if not origin_sys_val:
                        system_id = "analytics_platform"
                elif "support" in col_name_val:
                    record_type = "SUPPORT_MESSAGE"
                    if not origin_sys_val:
                        system_id = "support_platform"

                rid = row_dict.get("resource_id")
                updated_at_str = row_dict.get("updated_at")
                obs_ts = parse_iso_ts(updated_at_str) if updated_at_str else file_ts

                # Extract identifiers
                idents: Set[str] = set()
                pii_fields: Dict[str, str] = {}

                for uid_col in ["user_id", "customer_reference", "subject_reference"]:
                    val = row_dict.get(uid_col)
                    if val and str(val).strip():
                        u = str(val).strip()
                        idents.add(u)
                        row_dict[uid_col] = u

                for e_col in ["email", "customer_email", "requester_email", "owner_email"]:
                    val = row_dict.get(e_col)
                    if val and str(val).strip():
                        em = norm_email(val)
                        idents.add(em)
                        pii_fields[e_col] = em

                for p_col in ["phone", "requester_phone", "owner_phone"]:
                    val = row_dict.get(p_col)
                    if val and str(val).strip():
                        ph = norm_phone(val)
                        idents.add(ph)
                        pii_fields[p_col] = ph

                for h_col in ["email_hash"]:
                    val = row_dict.get(h_col)
                    if val and str(val).strip():
                        h = str(val).strip().lower()
                        idents.add(h)
                        pii_fields[h_col] = h

                for n_col in ["full_name", "display_name", "requester_name"]:
                    val = row_dict.get(n_col)
                    if val and str(val).strip():
                        nm = norm_name(val)
                        idents.add(nm)
                        pii_fields[n_col] = nm

                # Status computation per table type
                status = "PRESENT"
                if record_type == "DATA_FLOW":
                    enabled = row_dict.get("enabled")
                    status = "ACTIVE" if enabled in (1, "1", True, "true") else "DISABLED"
                elif record_type == "BACKUP_ARCHIVE":
                    restore_allowed = row_dict.get("restore_allowed")
                    status = "RESTORABLE" if restore_allowed in (1, "1", True, "true") else "BLOCKED"
                elif record_type == "SECURITY_AUDIT_LOG":
                    status = "RETAINED"
                else:
                    # PII bearing records
                    has_pii = bool(pii_fields)
                    has_user_ref = any(row_dict.get(c) for c in ["user_id", "customer_reference", "subject_reference"])
                    if has_pii:
                        status = "PRESENT"
                    elif has_user_ref:
                        status = "REDACTED"
                    else:
                        status = "ANONYMIZED"

                raw_fields = dict(row_dict)
                raw_fields["table"] = tbl
                raw_fields["replica_role"] = replica_role
                raw_fields["pii_fields"] = pii_fields

                observations.append(
                    Observation(
                        source_id=source_id,
                        source_kind="file",
                        observed_at=obs_ts,
                        citable_at=manifest_citable_at,
                        system_hint=system_id,
                        resource_id=rid,
                        record_type=record_type,
                        status=status,
                        identifiers=frozenset(idents),
                        fields=raw_fields,
                        is_claim=False,
                        raw_ref=f"{sql_path.name}:{tbl}:{row_idx}",
                    )
                )
    finally:
        conn.close()

    return observations
