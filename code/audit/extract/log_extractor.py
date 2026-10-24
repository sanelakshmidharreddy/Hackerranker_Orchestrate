import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..config import PREFIX_SYSTEM_CATEGORY
from ..loaders import norm_email, norm_phone, parse_iso_ts
from ..models import EvidenceFile, Observation

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
SHA256_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")
USER_ID_REGEX = re.compile(r"^user_\d+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s()-]{7,25}$")

KV_REGEX = re.compile(r'([a-zA-Z0-9_.-]+)=(?:"([^"]*)"|([^\s,]+))')
BRACKET_REGEX = re.compile(r"^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+([^:]+):\s*(.*)$")
PIPE_REGEX = re.compile(r"^(\S+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(.*)$")
SYSLOG_REGEX = re.compile(r"^(\S+)\s+<\d+>\d+\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-\s+(.*)$")

def parse_log_line_tokens(line: str) -> Dict[str, Any]:
    """Parse key=value pairs and contextual fields from a single log line."""
    line = line.strip()
    if not line:
        return {}

    tokens: Dict[str, Any] = {}

    # Extract leading timestamp
    ts_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)", line)
    if ts_match:
        tokens["timestamp"] = parse_iso_ts(ts_match.group(1))

    # Format 1: JSON line format after timestamp
    json_start = line.find("{")
    if json_start != -1 and line.endswith("}"):
        try:
            j_data = json.loads(line[json_start:])
            if isinstance(j_data, dict):
                tokens.update(j_data)
                if "timestamp" not in tokens and "time" in j_data:
                    tokens["timestamp"] = parse_iso_ts(j_data["time"])
                return tokens
        except Exception:
            pass

    # Format 2: Bracketed format: ts [LEVEL] [SERVICE] [TRACE] EVENT: ...
    bm = BRACKET_REGEX.match(line)
    if bm:
        ts_str, level, service, trace_id, event, rest = bm.groups()
        tokens["level"] = level.strip()
        tokens["service"] = service.strip()
        tokens["trace_id"] = trace_id.strip()
        tokens["event"] = event.strip()
        line_to_parse = rest
    else:
        # Format 3: Pipe format: ts | LEVEL | SERVICE | TRACE | EVENT | ...
        pm = PIPE_REGEX.match(line)
        if pm:
            ts_str, level, service, trace_id, event, rest = pm.groups()
            tokens["level"] = level.strip()
            tokens["service"] = service.strip()
            tokens["trace_id"] = trace_id.strip()
            tokens["event"] = event.strip()
            line_to_parse = rest
        else:
            # Format 4: Syslog format: ts <14>1 node-4 account_service tr-3269055 - - ...
            sm = SYSLOG_REGEX.match(line)
            if sm:
                ts_str, service, trace_id, rest = sm.groups()
                tokens["service"] = service.strip()
                tokens["trace_id"] = trace_id.strip()
                line_to_parse = rest
            else:
                line_to_parse = line

    # Parse all key="val" or key=val in line_to_parse
    for m in KV_REGEX.finditer(line_to_parse):
        k = m.group(1).strip()
        v = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
        tokens[k] = v

    # Check if message contains escaped nested key-values
    if "message" in tokens and isinstance(tokens["message"], str):
        msg = tokens["message"]
        for m in KV_REGEX.finditer(msg):
            k = m.group(1).strip()
            v = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
            if k not in tokens:
                tokens[k] = v

    # Clean quotes from values
    for k, v in list(tokens.items()):
        if isinstance(v, str):
            tokens[k] = v.strip('"\'')

    # Normalize trace_id / requestId
    if "requestId" in tokens and "trace_id" not in tokens:
        tokens["trace_id"] = tokens["requestId"]

    return tokens

def extract_log_evidence(
    log_path: Path,
    evidence_file: Optional[EvidenceFile] = None,
) -> List[Observation]:
    """Parse log evidence file and correlate traces into Observations."""
    observations: List[Observation] = []
    source_id = evidence_file.file_id if evidence_file else log_path.stem
    manifest_citable_at = (
        evidence_file.captured_at
        if evidence_file
        else datetime.min.replace(tzinfo=timezone.utc)
    )

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Pass 1: Parse tokens for all lines and group by trace_id
    traces: Dict[str, List[Dict[str, Any]]] = {}
    standalone_lines: List[Dict[str, Any]] = []

    for line_idx, line in enumerate(lines):
        tok = parse_log_line_tokens(line)
        if not tok:
            continue
        tok["_line_no"] = line_idx + 1
        trace_id = tok.get("trace_id")
        if trace_id and trace_id != "-":
            traces.setdefault(trace_id, []).append(tok)
        else:
            standalone_lines.append(tok)

    # Helper to process a trace event list
    def process_trace_events(events: List[Dict[str, Any]]) -> Optional[Observation]:
        # Carry keys across all lines in the trace
        combined_idents: Set[str] = set()
        trace_service = None
        trace_resource_id = None
        terminal_event = None
        recreation_event = None

        # Sort events chronologically
        events.sort(key=lambda x: x.get("timestamp") or manifest_citable_at)

        for e in events:
            if not trace_service:
                trace_service = e.get("service") or e.get("function")
            if not trace_resource_id:
                trace_resource_id = e.get("resource_id") or e.get("account_id") or e.get("target_id")

            # Collect identifier cues from all keys and values in the event
            for k, val in e.items():
                if val and isinstance(val, (str, int)):
                    val_str = str(val).strip()
                    lower_k = k.lower()
                    if EMAIL_REGEX.match(val_str):
                        combined_idents.add(norm_email(val_str))
                    elif USER_ID_REGEX.match(val_str):
                        combined_idents.add(val_str)
                    elif SHA256_REGEX.match(val_str):
                        combined_idents.add(val_str.lower())
                    elif PHONE_REGEX.match(val_str):
                        combined_idents.add(norm_phone(val_str))
                    elif any(sub in lower_k for sub in ["email", "user", "hash", "key", "subject", "requester"]):
                        if EMAIL_REGEX.match(val_str):
                            combined_idents.add(norm_email(val_str))
                        elif SHA256_REGEX.match(val_str):
                            combined_idents.add(val_str.lower())

            event_name = e.get("event", "")
            if "recreation" in event_name or "sync_delivery" in event_name or "restore_write" in event_name:
                recreation_event = e
            if "completed" in event_name or "result" in event_name or "finished" in event_name:
                terminal_event = e

        # If we have recreation event
        if recreation_event:
            ts = recreation_event.get("timestamp") or manifest_citable_at
            rid = trace_resource_id or recreation_event.get("resource_id")
            if rid:
                return Observation(
                    source_id=source_id,
                    source_kind="file",
                    observed_at=ts,
                    citable_at=manifest_citable_at,
                    system_hint=trace_service or "unknown_service",
                    resource_id=rid,
                    record_type=None,
                    status="PRESENT",
                    identifiers=frozenset(combined_idents),
                    fields=dict(recreation_event, recreated_by=recreation_event.get("event")),
                    is_claim=False,
                    raw_ref=f"{log_path.name}:{recreation_event.get('_line_no')}",
                )

        if not terminal_event:
            # Check if any event has rows=0 or rows>0 or status
            for e in reversed(events):
                if "rows" in e or "http_status" in e or "enabled" in e or "restore_allowed" in e:
                    terminal_event = e
                    break

        if not terminal_event:
            return None

        ts = terminal_event.get("timestamp") or manifest_citable_at
        rid = trace_resource_id or terminal_event.get("resource_id")
        if not rid:
            return None

        # Derive status
        status = "PRESENT"
        rows = terminal_event.get("rows")
        http_status = terminal_event.get("http_status")
        enabled = terminal_event.get("enabled")
        restore_allowed = terminal_event.get("restore_allowed")
        ev_result = str(terminal_event.get("result", "")).lower()
        ev_name = str(terminal_event.get("event", "")).lower()

        if rows is not None:
            try:
                r_int = int(rows)
                status = "ABSENT" if r_int == 0 else "PRESENT"
            except Exception:
                pass
        elif http_status is not None:
            if str(http_status) == "404":
                status = "ABSENT"
            elif str(http_status) in ("200", "204"):
                status = "PRESENT"
        elif ev_result == "hit":
            status = "PRESENT"
        elif ev_result == "miss":
            status = "ABSENT"

        if "pii_scan" in ev_name and terminal_event.get("matched_value"):
            status = "PRESENT"

        if enabled is not None:
            status = "ACTIVE" if enabled in (True, 1, "true", "1") else "DISABLED"
        if restore_allowed is not None:
            status = "RESTORABLE" if restore_allowed in (True, 1, "true", "1") else "BLOCKED"

        # System and record type resolution from rid prefix if service not clear
        system_id = trace_service
        record_type = None
        for prefix, (default_sys, default_cat) in PREFIX_SYSTEM_CATEGORY.items():
            if rid.startswith(prefix):
                if not system_id or system_id in ("log_router", "unknown_service"):
                    system_id = default_sys
                record_type = default_cat
                break

        return Observation(
            source_id=source_id,
            source_kind="file",
            observed_at=ts,
            citable_at=manifest_citable_at,
            system_hint=system_id,
            resource_id=rid,
            record_type=record_type,
            status=status,
            identifiers=frozenset(combined_idents),
            fields=dict(terminal_event),
            is_claim=False,
            raw_ref=f"{log_path.name}:{terminal_event.get('_line_no')}",
        )

    # Process all traces
    for trace_id, event_list in traces.items():
        obs = process_trace_events(event_list)
        if obs:
            observations.append(obs)

    # Process standalone lines with completed events
    for line_tok in standalone_lines:
        ev_name = line_tok.get("event", "")
        if "completed" in ev_name or "rows" in line_tok or "http_status" in line_tok:
            obs = process_trace_events([line_tok])
            if obs:
                observations.append(obs)

    return observations
