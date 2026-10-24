"""
PDF evidence extractor.

Strategy:
1. Try pypdf text extraction.
2. If text is too short (<50 chars) or all gibberish, fall back to LLM with
   a base64-encoded first page (images not attached — raw text prompt only
   since PDFs are renderable text in this dataset).
3. Parse the extracted text for structured record/detail table rows matching
   the Northstar Shop PDF layout (record | detail table rows).
4. Emit one Observation per identified resource (account, support_*, audit_*, etc.)
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set

_CODE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from config import PREFIX_SYSTEM_CATEGORY
from audit.loaders import norm_email, norm_name, norm_phone, parse_iso_ts
from audit.models import EvidenceFile, Observation

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
SHA256_REGEX = re.compile(r"[a-fA-F0-9]{64}")
USER_ID_REGEX = re.compile(r"\buser_\d+\b")
RESOURCE_ID_REGEX = re.compile(
    r"\b("
    r"account_\d+|search_\d+|support_\d+|analytics_\d+|audit_record_\d+|"
    r"audit_record_[a-zA-Z0-9_]+|data_flow_\d+|backup_\d+|export_\d+|"
    r"tombstone_\d+|cache_\d+|marketing_\d+|legal_\d+"
    r")\b"
)


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception as exc:
        return ""


def _llm_extract_pdf(pdf_path: Path, context_label: str) -> str:
    """Fall back to LLM for PDFs where pypdf yields insufficient text."""
    try:
        from audit.llm import call_llm
        text = _extract_pdf_text(pdf_path)
        prompt = (
            "Extract all structured facts from this PDF document for a deletion audit.\n"
            "List every person, email address, user ID, account ID, support ticket, "
            "audit record, backup, export, or analytics record you find.\n"
            "For each: state the record type, resource ID (if visible), status, "
            "and all identifiers (name, email, phone, user_id).\n"
            "Document text:\n"
            f"{text}\n\n"
            "Output as a simple bullet list."
        )
        result, _ = call_llm(prompt, context_label=context_label)
        return result
    except Exception as exc:
        return ""


def _parse_observations_from_text(
    text: str,
    source_id: str,
    file_ts: datetime,
    pdf_path: Path,
) -> List[Observation]:
    """Parse extracted PDF text into Observations."""
    observations: List[Observation] = []

    # Find all resource IDs mentioned
    resource_ids_found = set(RESOURCE_ID_REGEX.findall(text))

    # Find all identifiers
    emails_found = {norm_email(e) for e in EMAIL_REGEX.findall(text)}
    user_ids_found = set(USER_ID_REGEX.findall(text))
    sha_found = {s.lower() for s in SHA256_REGEX.findall(text)}

    # Find timestamps
    ts_match = re.search(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)", text
    )
    obs_ts = parse_iso_ts(ts_match.group(1)) if ts_match else file_ts

    # Find "retain until" indicators — if present, tag as RETAINED
    has_retain = bool(re.search(r"retain\s+until", text, re.IGNORECASE))
    # Status/event extraction
    status = "PRESENT"
    if re.search(r"\bclosure\s+recorded\b", text, re.IGNORECASE):
        status = "ABSENT"

    all_idents: Set[str] = emails_found | user_ids_found | sha_found

    for rid in resource_ids_found:
        # Determine system and record_type from prefix
        system_id = "unknown_service"
        record_type = None
        for prefix, (sys_name, cat) in PREFIX_SYSTEM_CATEGORY.items():
            if rid.startswith(prefix.rstrip("_") + "_"):
                system_id = sys_name
                record_type = cat
                break

        rec_status = "RETAINED" if (has_retain and record_type in ("SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD")) else status

        observations.append(
            Observation(
                source_id=source_id,
                source_kind="file",
                observed_at=obs_ts,
                citable_at=file_ts,
                system_hint=system_id,
                resource_id=rid,
                record_type=record_type,
                status=rec_status,
                identifiers=frozenset(all_idents),
                fields={"pdf_path": str(pdf_path), "text_snippet": text[:200]},
                is_claim=False,
                raw_ref=pdf_path.name,
            )
        )

    # If no resource IDs found but identifiers exist, emit a single generic observation
    if not resource_ids_found and all_idents:
        observations.append(
            Observation(
                source_id=source_id,
                source_kind="file",
                observed_at=obs_ts,
                citable_at=file_ts,
                system_hint="document_store",
                resource_id=None,
                record_type="DOCUMENT",
                status=status,
                identifiers=frozenset(all_idents),
                fields={"pdf_path": str(pdf_path), "text_snippet": text[:200]},
                is_claim=False,
                raw_ref=pdf_path.name,
            )
        )

    return observations


def extract_pdf_evidence(
    pdf_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Extract Observations from a PDF evidence file."""
    source_id = evidence_file.file_id if evidence_file else pdf_path.stem
    file_ts = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    # Step 1: pypdf text extraction
    text = _extract_pdf_text(pdf_path)

    # Step 2: if text is very short, try LLM
    if len(text.strip()) < 50:
        text = _llm_extract_pdf(pdf_path, context_label=f"pdf:{source_id}")

    if not text.strip():
        return []

    return _parse_observations_from_text(text, source_id, file_ts, pdf_path)
