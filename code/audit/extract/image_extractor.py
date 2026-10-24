"""
Image evidence extractor (Phase 2).

All 11 screenshots are admin/inspection consoles. Each image is passed to the
LLM (cached by sha256) with a structured extraction prompt.

The LLM is asked to return a JSON list of observations matching the schema:
  [{"resource_id": "...", "system": "...", "status": "...", "identifiers": [...],
    "record_type": "...", "timestamp": "..."}]

Falls back to an empty list if LLM is unavailable.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_CODE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from config import PREFIX_SYSTEM_CATEGORY
from audit.loaders import norm_email, norm_phone, parse_iso_ts
from audit.models import EvidenceFile, Observation

_IMAGE_PROMPT = """\
You are an evidence extractor for a data deletion audit.
Analyse this screenshot from a Northstar Shop admin console.

Extract every visible record, table row, or entry and output a JSON array.
Each element must have these fields:
  "resource_id"  - the visible record or account ID (e.g. "account_005", "search_001"); null if not visible
  "system"       - the service this record belongs to (e.g. "account_service", "search_service",
                   "analytics_platform", "support_platform", "backup_service", "export_service",
                   "integration_service", "security_service", "identity_service")
  "record_type"  - e.g. "USER_PROFILE", "SEARCH_INDEX_ENTRY", "ANALYTICS_PROFILE",
                   "SUPPORT_MESSAGE", "BACKUP_ARCHIVE", "USER_EXPORT", "DATA_FLOW",
                   "SECURITY_AUDIT_LOG", "ACCOUNT_TOMBSTONE"
  "status"       - one of: PRESENT, ABSENT, REDACTED, ANONYMIZED, ACTIVE, DISABLED, RESTORABLE, BLOCKED
  "identifiers"  - list of emails, user_ids (user_NNN), phone numbers visible for this record
  "timestamp"    - ISO-8601 timestamp if visible, else null

Return ONLY valid JSON. No markdown, no commentary. Example:
[{"resource_id":"account_005","system":"account_service","record_type":"USER_PROFILE",
  "status":"PRESENT","identifiers":["leila.haddad@yahoo.com","user_05"],"timestamp":null}]
"""

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
USER_ID_REGEX = re.compile(r"\buser_\d+\b")


def extract_image_evidence(
    image_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Extract Observations from a screenshot using LLM (cached)."""
    source_id = evidence_file.file_id if evidence_file else image_path.stem
    file_ts = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    # Call LLM (cached by sha256 of image bytes + prompt)
    try:
        from audit.llm import call_llm
        text, _ = call_llm(
            prompt=_IMAGE_PROMPT,
            image_paths=[image_path],
            context_label=f"image:{source_id}",
        )
    except Exception as exc:
        import sys
        print(f"[image_extractor] LLM unavailable for {source_id}: {exc}", file=sys.stderr)
        return []

    # Parse JSON response
    records = []
    try:
        # Strip markdown fences if present
        clean = re.sub(r"```(?:json)?\n?", "", text).strip()
        if clean.endswith("```"):
            clean = clean[:-3].strip()
        records = json.loads(clean)
        if not isinstance(records, list):
            records = []
    except Exception:
        # Try to extract JSON array from middle of text
        m = re.search(r"\[.*\]", text, re.DOTALL)
        if m:
            try:
                records = json.loads(m.group(0))
            except Exception:
                records = []

    observations: List[Observation] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue

        rid = rec.get("resource_id")
        status_raw = str(rec.get("status", "PRESENT")).upper()
        valid_statuses = {
            "PRESENT", "ABSENT", "REDACTED", "ANONYMIZED",
            "ACTIVE", "DISABLED", "RESTORABLE", "BLOCKED", "RETAINED"
        }
        status = status_raw if status_raw in valid_statuses else "PRESENT"

        # Identifiers
        raw_idents = rec.get("identifiers", [])
        if isinstance(raw_idents, str):
            raw_idents = [raw_idents]
        idents = set()
        for raw in raw_idents:
            raw = str(raw).strip()
            if EMAIL_REGEX.match(raw):
                idents.add(norm_email(raw))
            elif USER_ID_REGEX.match(raw):
                idents.add(raw)
            else:
                idents.add(raw)

        # System/record_type from prefix if not provided
        system_id = rec.get("system", "")
        record_type = rec.get("record_type")
        if rid and (not system_id or not record_type):
            for prefix, (sys_name, cat) in PREFIX_SYSTEM_CATEGORY.items():
                if rid.startswith(prefix.rstrip("_") + "_"):
                    if not system_id:
                        system_id = sys_name
                    if not record_type:
                        record_type = cat
                    break

        # Timestamp
        ts_raw = rec.get("timestamp")
        obs_ts = parse_iso_ts(ts_raw) if ts_raw else file_ts

        observations.append(
            Observation(
                source_id=source_id,
                source_kind="file",
                observed_at=obs_ts,
                citable_at=file_ts,
                system_hint=system_id or "unknown_service",
                resource_id=rid,
                record_type=record_type,
                status=status,
                identifiers=frozenset(idents),
                fields={"image_path": str(image_path), "llm_raw": rec},
                is_claim=False,
                raw_ref=image_path.name,
            )
        )

    return observations
