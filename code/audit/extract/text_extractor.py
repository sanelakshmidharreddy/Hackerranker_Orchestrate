import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set

from ..loaders import norm_email, parse_iso_ts
from ..models import EvidenceFile, Observation

LINE_REGEX = re.compile(
    r"^[-\s]*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(.*)$"
)

def extract_text_evidence(
    text_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Parse pipe-delimited text handover records."""
    observations: List[Observation] = []
    source_id = evidence_file.file_id if evidence_file else text_path.stem
    manifest_citable_at = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    with open(text_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Look for header snapshot timestamp
    header_ts = manifest_citable_at
    for line in lines[:10]:
        m = re.search(r"Snapshot:\s*(\S+)", line)
        if m:
            header_ts = parse_iso_ts(m.group(1))
            break

    for line_idx, line in enumerate(lines):
        line = line.strip()
        m = LINE_REGEX.match(line)
        if not m:
            continue
        ts_str, system, rid, record_type, result, subject = m.groups()
        obs_ts = parse_iso_ts(ts_str) if ts_str else header_ts
        system = system.strip()
        rid = rid.strip()
        record_type = record_type.strip()
        result = result.strip().upper()
        subject = subject.strip()

        # Map result to status
        status = "PRESENT"
        if result in ("NOT_FOUND", "ABSENT"):
            status = "ABSENT"
        elif result in ("FOUND", "PRESENT", "IDENTIFIABLE"):
            status = "PRESENT"
        elif result in ("ANONYMIZED",):
            status = "ANONYMIZED"
        elif result in ("REDACTED",):
            status = "REDACTED"
        elif result in ("ACTIVE", "ENABLED"):
            status = "ACTIVE"
        elif result in ("DISABLED",):
            status = "DISABLED"
        elif result in ("BLOCKED",):
            status = "BLOCKED"
        elif result in ("RESTORABLE",):
            status = "RESTORABLE"

        idents: Set[str] = set()
        if subject and subject.lower() != "no direct identifier":
            if "@" in subject:
                idents.add(norm_email(subject))
            elif subject.startswith("user_"):
                idents.add(subject)
            else:
                idents.add(subject)

        observations.append(
            Observation(
                source_id=source_id,
                source_kind="file",
                observed_at=obs_ts,
                citable_at=manifest_citable_at,
                system_hint=system,
                resource_id=rid,
                record_type=record_type,
                status=status,
                identifiers=frozenset(idents),
                fields={"result": result, "subject": subject},
                is_claim=False,
                raw_ref=f"{text_path.name}:{line_idx+1}",
            )
        )

    return observations
