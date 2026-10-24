import os
import sys
import csv
import json
import sqlite3
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 for console output on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_DIR = DATASET_DIR / "evidence"

def profile():
    report_lines = []
    def log(msg=""):
        try:
            print(msg)
        except Exception:
            print(str(msg).encode('ascii', errors='replace').decode('ascii'))
        report_lines.append(str(msg))

    log("=" * 80)
    log("GHOST DATA STILL EXISTS — DATASET PROFILING REPORT")
    log("=" * 80)

    # 1. Row counts of every CSV in dataset/
    log("\n### 1. CSV Row Counts in dataset/")
    csv_files = sorted(DATASET_DIR.glob("*.csv"))
    csv_row_counts = {}
    for f in csv_files:
        with open(f, "r", encoding="utf-8") as fp:
            reader = csv.reader(fp)
            header = next(reader, None)
            count = sum(1 for _ in reader)
            csv_row_counts[f.name] = (count, header)
            log(f"  - {f.name}: {count} data rows | Header: {header}")

    # 2. Value counts of reported_status, event_type, reported_result, source_system, target_system, field_name
    log("\n### 2. Value Counts from CSVs")
    
    # 2.1 deletion_requests.csv: reported_status
    del_req_file = DATASET_DIR / "deletion_requests.csv"
    reported_statuses = Counter()
    request_texts = Counter()
    eval_case_ids = []
    with open(del_req_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            eval_case_ids.append(row["case_id"])
            reported_statuses[row["reported_status"]] += 1
            request_texts[row["request_text"]] += 1

    log(f"\n* deletion_requests.csv reported_status (total {sum(reported_statuses.values())}):")
    for k, v in reported_statuses.most_common():
        log(f"    {k}: {v}")

    # 2.2 sample_deletion_requests.csv
    sample_req_file = DATASET_DIR / "sample_deletion_requests.csv"
    sample_statuses = Counter()
    if sample_req_file.exists():
        with open(sample_req_file, "r", encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                sample_statuses[row["reported_status"]] += 1
        log(f"\n* sample_deletion_requests.csv reported_status (total {sum(sample_statuses.values())}):")
        for k, v in sample_statuses.most_common():
            log(f"    {k}: {v}")

    # 2.3 sample_output.csv: deletion_status
    sample_out_file = DATASET_DIR / "sample_output.csv"
    sample_out_statuses = Counter()
    if sample_out_file.exists():
        with open(sample_out_file, "r", encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                sample_out_statuses[row["deletion_status"]] += 1
        log(f"\n* sample_output.csv deletion_status (total {sum(sample_out_statuses.values())}):")
        for k, v in sample_out_statuses.most_common():
            log(f"    {k}: {v}")

    # 2.4 system_activity.csv
    sys_act_file = DATASET_DIR / "system_activity.csv"
    event_types = Counter()
    reported_results = Counter()
    source_systems = Counter()
    target_systems = Counter()
    resource_prefixes = Counter()
    with open(sys_act_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            event_types[row["event_type"]] += 1
            reported_results[row["reported_result"]] += 1
            source_systems[row["source_system"]] += 1
            target_systems[row["target_system"]] += 1
            rid = row.get("resource_id", "").strip()
            if rid:
                prefix = rid.split("_")[0] + "_" if "_" in rid else "NO_PREFIX"
                resource_prefixes[prefix] += 1

    log(f"\n* system_activity.csv event_type (total {sum(event_types.values())}):")
    for k, v in event_types.most_common():
        log(f"    {k:28s}: {v}")

    log(f"\n* system_activity.csv reported_result (total {sum(reported_results.values())}):")
    for k, v in reported_results.most_common():
        log(f"    {k:15s}: {v}")

    log(f"\n* system_activity.csv target_system (top 15 of {len(target_systems)}):")
    for k, v in target_systems.most_common(15):
        log(f"    {k:30s}: {v}")

    log(f"\n* system_activity.csv source_system (top 15 of {len(source_systems)}):")
    for k, v in source_systems.most_common(15):
        log(f"    {k:30s}: {v}")

    log(f"\n* system_activity.csv resource_id prefixes:")
    for k, v in resource_prefixes.most_common():
        log(f"    {k:20s}: {v}")

    # 2.5 user_audit_log.csv
    audit_file = DATASET_DIR / "user_audit_log.csv"
    field_names = Counter()
    with open(audit_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            field_names[row["field_name"]] += 1

    log(f"\n* user_audit_log.csv field_name (total {sum(field_names.values())}):")
    for k, v in field_names.most_common():
        log(f"    {k:15s}: {v}")

    # 3. Request texts analysis
    log(f"\n### 3. Distinct request_text Values in deletion_requests.csv ({len(request_texts)} distinct)")
    log(f"{'Count':<6} | {'First 80 characters':<80}")
    log("-" * 90)
    for txt, cnt in request_texts.most_common():
        preview = repr(txt[:80].strip())[1:-1]
        log(f"{cnt:<6} | {preview}")

    # 4. Email hash verification
    log("\n### 4. Email Hash Verification (user_identities.csv)")
    identities_file = DATASET_DIR / "user_identities.csv"
    hash_mismatches = 0
    total_users = 0
    with open(identities_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            total_users += 1
            norm_e = row["email"].strip().lower()
            expected = hashlib.sha256(norm_e.encode("utf-8")).hexdigest()
            if row["email_hash"] != expected:
                hash_mismatches += 1
    log(f"  Total users checked: {total_users}")
    log(f"  Email hash mismatches: {hash_mismatches}")

    # 5. Evidence files manifest analysis
    log("\n### 5. Evidence Files Manifest (evidence_files.csv)")
    ev_file = DATASET_DIR / "evidence_files.csv"
    folders = Counter()
    origins = Counter()
    timestamps = []
    with open(ev_file, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            p = row["file_path"].replace("\\", "/")
            folder = p.split("/")[0] if "/" in p else "root"
            folders[folder] += 1
            origins[row["origin"]] += 1
            timestamps.append(row["captured_at"])

    log(f"  Total evidence files: {len(timestamps)}")
    log("  Counts by folder:")
    for f, c in folders.most_common():
        log(f"    {f:15s}: {c}")
    log("  Counts by origin:")
    for o, c in origins.most_common():
        log(f"    {o:30s}: {c}")
    log(f"  Min captured_at: {min(timestamps)}")
    log(f"  Max captured_at: {max(timestamps)}")

    # 6. SQL files analysis
    log("\n### 6. SQL Files Analysis (.sql under evidence/databases/)")
    sql_dir = EVIDENCE_DIR / "databases"
    sql_files = sorted(sql_dir.glob("*.sql"))
    log(f"  Found {len(sql_files)} SQL files.")
    all_sql_tables = Counter()
    for sf in sql_files:
        conn = sqlite3.connect(":memory:")
        try:
            with open(sf, "r", encoding="utf-8") as f:
                content = f.read()
            conn.executescript(content)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]
            table_info = []
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                cnt = cur.fetchone()[0]
                table_info.append(f"{t}({cnt})")
                all_sql_tables[t] += 1
            log(f"  - {sf.name}: {', '.join(table_info) if table_info else 'EMPTY'}")
        except Exception as e:
            log(f"  - {sf.name}: ERROR loading sqlite - {e}")
        finally:
            conn.close()

    log("\n  Aggregated SQL table occurrences across all files:")
    for t, c in all_sql_tables.most_common():
        log(f"    {t:30s}: seen in {c} files")

    # 7. JSON files analysis
    log("\n### 7. JSON Files Analysis (.json under evidence/records/)")
    json_dir = EVIDENCE_DIR / "records"
    json_files = sorted(json_dir.glob("*.json"))
    log(f"  Found {len(json_files)} JSON files.")
    nested_shapes = set()
    status_values = Counter()

    def inspect_dict(d):
        if not isinstance(d, dict):
            return
        if "resource_id" in d:
            nested_shapes.add(tuple(sorted(d.keys())))
            for k in ["result", "state", "status", "enabled", "restore_allowed", "account_status"]:
                if k in d:
                    status_values[(k, str(d[k]))] += 1
        for v in d.values():
            if isinstance(v, dict):
                inspect_dict(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        inspect_dict(item)

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            top_keys = list(data.keys()) if isinstance(data, dict) else [f"array[{len(data)}]"]
            log(f"  - {jf.name}: Top-level keys: {top_keys}")
            if isinstance(data, dict):
                inspect_dict(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        inspect_dict(item)
        except Exception as e:
            log(f"  - {jf.name}: ERROR reading JSON - {e}")

    log(f"\n  Unique dictionary shapes containing 'resource_id' ({len(nested_shapes)} shapes):")
    for shape in sorted(nested_shapes, key=lambda s: len(s)):
        log(f"    {shape}")

    log("\n  Status/Result key-value counts observed in JSON:")
    for (k, val), cnt in status_values.most_common():
        log(f"    {k} = {val}: {cnt}")

    # 8. Log files analysis
    log("\n### 8. Log Files Analysis (.log under evidence/logs/)")
    log_dir = EVIDENCE_DIR / "logs"
    log_files = sorted(log_dir.glob("*.log"))
    log(f"  Found {len(log_files)} LOG files.")
    event_values = Counter()
    service_values = Counter()
    for lf in log_files:
        file_events = set()
        file_services = set()
        try:
            with open(lf, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    for m in re.finditer(r'(?:event|service)=([^\s]+)', line):
                        val = m.group(1).strip('"\'')
                        if line[m.start():].startswith('event='):
                            event_values[val] += 1
                            file_events.add(val)
                        elif line[m.start():].startswith('service='):
                            service_values[val] += 1
                            file_services.add(val)
            log(f"  - {lf.name}: services={file_services}, events={file_events}")
        except Exception as e:
            log(f"  - {lf.name}: ERROR reading log - {e}")

    log("\n  Top event= values across all log files:")
    for ev, c in event_values.most_common():
        log(f"    {ev:35s}: {c}")

    log("\n  Top service= values across all log files:")
    for svc, c in service_values.most_common():
        log(f"    {svc:30s}: {c}")

    # 9. PDF extraction
    log("\n### 9. PDF Files Analysis (.pdf under evidence/documents/)")
    doc_dir = EVIDENCE_DIR / "documents"
    pdf_files = sorted(doc_dir.glob("*.pdf"))
    log(f"  Found {len(pdf_files)} PDF files.")
    
    # Try pypdf or pdfplumber or fitz or basic regex fallback
    pdf_reader_mod = None
    try:
        import pypdf
        pdf_reader_mod = "pypdf"
    except ImportError:
        pass

    for pf in pdf_files:
        log(f"\n--- PDF: {pf.name} ---")
        extracted_lines = []
        if pdf_reader_mod == "pypdf":
            try:
                reader = pypdf.PdfReader(str(pf))
                log(f"  [pypdf] Pages: {len(reader.pages)}")
                full_text = ""
                for page in reader.pages:
                    full_text += (page.extract_text() or "") + "\n"
                extracted_lines = full_text.splitlines()
            except Exception as e:
                log(f"  [pypdf error] {e}")
        
        if not extracted_lines:
            # Fallback raw text stream extraction
            try:
                with open(pf, "rb") as f:
                    raw = f.read().decode("latin1", errors="replace")
                # find strings in parentheses or between BT and ET
                matches = re.findall(r'\((.*?)\)', raw)
                extracted_lines = [m for m in matches if len(m) > 3][:100]
            except Exception as e:
                log(f"  [raw error] {e}")

        log(f"  Showing up to 40 lines from {pf.name}:")
        for idx, line in enumerate(extracted_lines[:40]):
            log(f"    [{idx+1:02d}] {line.strip()}")

    # 10. Deletion Rules summary
    log("\n### 10. Deletion Rules (deletion_rules.csv)")
    rules_file = DATASET_DIR / "deletion_rules.csv"
    with open(rules_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rid = r.get('rule_id') or r.get('rule') or ''
            log(f"  - {rid:7s} | {r['data_category']:22s} | {r['required_action']:10s} | Condition: {r['condition']}")

    # Save Markdown report
    eval_dir = REPO_ROOT / "code" / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    notes_file = eval_dir / "notes_dataset.md"
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    log(f"\n[OK] Wrote full dataset notes to {notes_file}")

if __name__ == "__main__":
    profile()
