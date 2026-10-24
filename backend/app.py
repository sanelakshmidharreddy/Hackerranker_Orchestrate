"""
FastAPI Backend for Ghost Data Still Exists: Deletion-Audit Explorer.

Read-only auditor backend that exposes audit results, summary metrics,
and detailed evidence-backed case findings without mutating any dataset.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Resolve Repository Root (parent directory of backend/)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

app = FastAPI(
    title="Ghost Data Still Exists - Deletion Audit API",
    description="Read-only independent audit explorer for personal data deletion verification.",
    version="1.0.0",
)

# Configure CORS
DEFAULT_ORIGINS = [
    "https://hackerrankerorchestrate-frontend.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "")
env_origins = [origin.strip() for origin in FRONTEND_ORIGIN.split(",") if origin.strip()]
origins = list(dict.fromkeys(DEFAULT_ORIGINS + env_origins))
if "*" in env_origins or "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory data caches
DATA = {
    "cases": {},             # case_id -> merged dict
    "evidence_files": {},    # file_id -> {file_path, origin, captured_at}
    "summary": {},
}


def case_sort_key(cid: str) -> int:
    """Natural numeric sort by the integer after case_."""
    try:
        if "_" in cid:
            num = cid.split("_", 1)[1]
            if num.isdigit():
                return int(num)
    except Exception:
        pass
    return 999999


def load_dataset_and_results():
    """Load and index requests, audit outputs, and evidence manifest."""
    # 1. Load evidence manifest
    evidence_manifest_path = REPO_ROOT / "dataset" / "evidence_files.csv"
    evidence_files = {}
    if evidence_manifest_path.exists():
        with open(evidence_manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get("file_id")
                if fid:
                    evidence_files[fid] = {
                        "file_id": fid,
                        "file_path": row.get("file_path", ""),
                        "origin": row.get("origin", ""),
                        "captured_at": row.get("captured_at", ""),
                    }
    DATA["evidence_files"] = evidence_files

    # 2. Load requests (try deletion_requests.csv, fallback to sample_deletion_requests.csv)
    requests_path = REPO_ROOT / "dataset" / "deletion_requests.csv"
    if not requests_path.exists():
        requests_path = REPO_ROOT / "dataset" / "sample_deletion_requests.csv"

    requests_by_id = {}
    if requests_path.exists():
        with open(requests_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("case_id")
                if cid:
                    requests_by_id[cid] = row

    # Also load sample_deletion_requests.csv if different
    sample_requests_path = REPO_ROOT / "dataset" / "sample_deletion_requests.csv"
    if sample_requests_path.exists() and sample_requests_path != requests_path:
        with open(sample_requests_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("case_id")
                if cid and cid not in requests_by_id:
                    requests_by_id[cid] = row

    # 3. Load audit outputs from output.csv
    output_path = REPO_ROOT / "output.csv"
    outputs_by_id = {}
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("case_id")
                if cid:
                    outputs_by_id[cid] = row

    # Fallback to dataset/sample_output.csv if output.csv missing entries
    sample_output_path = REPO_ROOT / "dataset" / "sample_output.csv"
    if sample_output_path.exists():
        with open(sample_output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("case_id")
                if cid and cid not in outputs_by_id:
                    outputs_by_id[cid] = row

    # 4. Merge into unified case store
    all_case_ids = sorted(
        set(requests_by_id.keys()) | set(outputs_by_id.keys()),
        key=case_sort_key,
    )

    merged_cases = {}
    complete_count = 0
    incomplete_count = 0
    na_count = 0
    false_complete_count = 0

    for cid in all_case_ids:
        req = requests_by_id.get(cid, {})
        out = outputs_by_id.get(cid, {})

        reported_status = req.get("reported_status", "UNKNOWN")
        deletion_status = out.get("deletion_status", "UNKNOWN")

        # Parse steps_json
        raw_steps = out.get("steps_json", "[]")
        try:
            steps = json.loads(raw_steps) if raw_steps else []
        except Exception:
            steps = []

        findings = [s for s in steps if s.get("phase") == "FINDING"]
        plan = [s for s in steps if s.get("phase") == "REMEDIATION"]
        checks = [s for s in steps if s.get("phase") == "VERIFICATION"]

        # Track metrics
        if deletion_status == "COMPLETE":
            complete_count += 1
        elif deletion_status == "INCOMPLETE":
            incomplete_count += 1
            if reported_status == "COMPLETE":
                false_complete_count += 1
        elif deletion_status == "NOT_APPLICABLE":
            na_count += 1

        merged_cases[cid] = {
            "case_id": cid,
            "email": req.get("email", ""),
            "requested_at": req.get("requested_at", ""),
            "reported_status": reported_status,
            "reported_at": req.get("reported_at", ""),
            "audit_at": req.get("audit_at", ""),
            "request_text": req.get("request_text", ""),
            "deletion_status": deletion_status,
            "n_findings": len(findings),
            "findings": findings,
            "plan": plan,
            "checks": checks,
            "steps": steps,
        }

    DATA["cases"] = merged_cases
    DATA["summary"] = {
        "total_cases": len(merged_cases),
        "complete_count": complete_count,
        "incomplete_count": incomplete_count,
        "not_applicable_count": na_count,
        "false_complete_discrepancy_count": false_complete_count,
    }


@app.on_event("startup")
def startup_event():
    load_dataset_and_results()


@app.get("/")
def root():
    return {
        "app": "Ghost Data Still Exists - Deletion Audit API",
        "health": "/api/health",
        "summary": "/api/summary",
        "cases": "/api/cases",
    }


@app.get("/api/health")
@app.get("/health")
def get_health():
    return {
        "status": "ok",
        "total_cases_indexed": len(DATA.get("cases", {})),
        "evidence_files_indexed": len(DATA.get("evidence_files", {})),
    }


@app.get("/api/summary")
def get_summary():
    if not DATA["summary"]:
        load_dataset_and_results()
    return DATA["summary"]


@app.get("/api/cases")
def list_cases(
    status: Optional[str] = Query(None, description="Filter by deletion_status (COMPLETE, INCOMPLETE, NOT_APPLICABLE)"),
    q: Optional[str] = Query(None, description="Search query across case_id or email"),
):
    if not DATA["cases"]:
        load_dataset_and_results()

    results = []
    status_filter = status.strip().upper() if status else None
    query_filter = q.strip().lower() if q else None

    for cid, c in DATA["cases"].items():
        if status_filter and c["deletion_status"].upper() != status_filter:
            continue
        if query_filter:
            matches_id = query_filter in c["case_id"].lower()
            matches_email = query_filter in c["email"].lower()
            if not (matches_id or matches_email):
                continue

        results.append({
            "case_id": c["case_id"],
            "email": c["email"],
            "reported_status": c["reported_status"],
            "deletion_status": c["deletion_status"],
            "n_findings": c["n_findings"],
            "audit_at": c["audit_at"],
        })

    return results


@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: str):
    if not DATA["cases"]:
        load_dataset_and_results()

    case = DATA["cases"].get(case_id.strip())
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    manifest = DATA.get("evidence_files", {})

    def expand_step(step: dict) -> dict:
        ev_id = step.get("evidence_id", "")
        expanded = dict(step)
        if ev_id and ev_id in manifest:
            meta = manifest[ev_id]
            expanded["evidence_meta"] = {
                "file_path": meta["file_path"],
                "origin": meta["origin"],
                "captured_at": meta["captured_at"],
            }
        else:
            expanded["evidence_meta"] = None
        return expanded

    expanded_findings = [expand_step(s) for s in case["findings"]]
    expanded_plan = [expand_step(s) for s in case["plan"]]
    expanded_checks = [expand_step(s) for s in case["checks"]]

    return {
        "case_id": case["case_id"],
        "email": case["email"],
        "requested_at": case["requested_at"],
        "reported_status": case["reported_status"],
        "reported_at": case["reported_at"],
        "audit_at": case["audit_at"],
        "request_text": case["request_text"],
        "deletion_status": case["deletion_status"],
        "n_findings": case["n_findings"],
        "findings": expanded_findings,
        "plan_label": "Recommended plan (not executed)",
        "plan": expanded_plan,
        "checks": expanded_checks,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
