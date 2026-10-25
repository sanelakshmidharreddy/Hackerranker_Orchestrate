"""
Main entry point for the Ghost Data Still Exists deletion audit agent.

Usage:
    python code/main.py                   # Process all 518 cases
    python code/main.py --cases sample    # Process 32 sample cases only
    python code/main.py --cases case_05   # Process a single case
    python code/main.py --no-multimodal   # Skip image/PDF LLM extraction

Output: output.csv at repo root
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure code/ on sys.path
_CODE_DIR = Path(__file__).resolve().parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(_CODE_DIR.parent / ".env")
except Exception:
    pass

from config import DATASET_DIR, CACHE_DIR
from audit.loaders import (
    load_deletion_requests,
    load_deletion_rules,
    load_user_identities,
    load_user_audit_log,
    load_evidence_manifest,
    case_sort_key,
)
from audit.ingest import build_observation_store
from audit.intent import classify_intent
from audit.identity import resolve_identity
from audit.state import reconstruct_state
from audit.policy import load_policy
from audit.planner import build_step_list, Step


def dump_steps(steps: list) -> str:
    """Serialize steps to compact JSON string."""
    return json.dumps(
        [s.to_dict() for s in steps],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def process_case(
    case,
    store,
    policy,
    identity_rows,
    audit_log_rows,
    verbose: bool = False,
) -> dict:
    """Process a single deletion audit case."""
    t_start = time.time()

    # Phase 3a: Intent classification
    intent = classify_intent(case.request_text, case_id=case.case_id)
    if intent == "NOT_APPLICABLE":
        return {
            "case_id": case.case_id,
            "deletion_status": "NOT_APPLICABLE",
            "steps_json": "[]",
            "elapsed": time.time() - t_start,
        }

    # Phase 3b: Identity resolution
    identity = resolve_identity(
        case_email=case.email,
        audit_at=case.audit_at,
        identity_rows=identity_rows,
        audit_log_rows=audit_log_rows,
    )

    if verbose:
        print(f"  [{case.case_id}] identity: {identity}")

    # Phase 4a: State reconstruction
    states = reconstruct_state(
        identity_ids=identity.all_identifiers,
        audit_at=case.audit_at,
        store=store,
    )

    if verbose:
        print(f"  [{case.case_id}] found {len(states)} resources:")
        for rid, rs in sorted(states.items()):
            print(f"    {rid}: {rs.status} (claim={rs.is_claim}, rec={rs.was_recreated})")

    # Phase 4b: Plan steps
    steps = build_step_list(
        states=states,
        policy=policy,
        deletion_status="DELETION",  # already checked NOT_APPLICABLE above
    )

    # Determine final status
    finding_steps = [s for s in steps if s.phase == "FINDING"]
    if finding_steps:
        deletion_status = "INCOMPLETE"
    elif getattr(case, "reported_status", "") == "NOT_STARTED":
        # Cases with workflow_claim NOT_STARTED should never be COMPLETE.
        deletion_status = "INCOMPLETE"
    else:
        deletion_status = "COMPLETE"

    return {
        "case_id": case.case_id,
        "deletion_status": deletion_status,
        "steps_json": dump_steps(steps),
        "elapsed": time.time() - t_start,
    }


def main():
    parser = argparse.ArgumentParser(description="Ghost Data Still Exists - Deletion Audit Agent")
    parser.add_argument(
        "--cases",
        default="all",
        help="'all', 'sample', or specific case_id",
    )
    parser.add_argument(
        "--no-multimodal",
        action="store_true",
        help="Skip image/PDF LLM extraction (faster, no API calls needed)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-case debug info",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: repo root output.csv)",
    )
    args = parser.parse_args()

    include_multimodal = not args.no_multimodal
    repo_root = _CODE_DIR.parent
    output_path = Path(args.output) if args.output else (repo_root / "output.csv")

    print(f"[main] Starting audit agent — {datetime.now(timezone.utc).isoformat()}")
    print(f"[main] Dataset: {DATASET_DIR}")
    print(f"[main] Multimodal LLM: {include_multimodal}")

    # Load CSV data
    print("[main] Loading CSV datasets...")
    all_cases = load_deletion_requests(DATASET_DIR / "deletion_requests.csv")
    identity_rows = load_user_identities(DATASET_DIR / "user_identities.csv")
    audit_log_rows = load_user_audit_log(DATASET_DIR / "user_audit_log.csv")
    policy = load_policy(DATASET_DIR / "deletion_rules.csv")

    # Filter cases
    if args.cases == "sample":
        sample_file = DATASET_DIR / "sample_deletion_requests.csv"
        cases = load_deletion_requests(sample_file)
        cases.sort(key=lambda c: case_sort_key(c.case_id))
    elif args.cases == "all":
        cases = sorted(all_cases, key=lambda c: case_sort_key(c.case_id))
    else:
        # Specific case_id
        target = args.cases.strip()
        cases = [c for c in all_cases if c.case_id == target]
        if not cases:
            # Also check sample_deletion_requests.csv
            sample_file = DATASET_DIR / "sample_deletion_requests.csv"
            sample_cases = load_deletion_requests(sample_file)
            cases = [c for c in sample_cases if c.case_id == target]
        if not cases:
            print(f"[main] ERROR: case_id '{target}' not found in deletion_requests.csv or sample_deletion_requests.csv", file=sys.stderr)
            sys.exit(1)

    print(f"[main] Processing {len(cases)} cases...")

    # Build observation store (Phase 1+2)
    print("[main] Building observation store (ingesting all evidence)...")
    t_ingest = time.time()
    store = build_observation_store(
        dataset_dir=DATASET_DIR,
        include_activity=True,
        include_multimodal=include_multimodal,
    )
    print(f"[main] Ingested {len(store.get_all_observations())} observations in {time.time() - t_ingest:.1f}s")

    # Process each case
    results = []
    t_all = time.time()
    for i, case in enumerate(cases):
        if args.verbose:
            print(f"\n[case] {case.case_id} | email={case.email} | audit_at={case.audit_at.isoformat()}")
        try:
            result = process_case(
                case=case,
                store=store,
                policy=policy,
                identity_rows=identity_rows,
                audit_log_rows=audit_log_rows,
                verbose=args.verbose,
            )
        except Exception as exc:
            print(f"[main] ERROR on {case.case_id}: {exc}", file=sys.stderr)
            import traceback; traceback.print_exc(file=sys.stderr)
            result = {
                "case_id": case.case_id,
                "deletion_status": "INCOMPLETE",
                "steps_json": "[]",
                "elapsed": 0,
            }
        results.append(result)

        if (i + 1) % 50 == 0:
            elapsed = time.time() - t_all
            rate = (i + 1) / elapsed
            remaining = (len(cases) - i - 1) / rate if rate > 0 else 0
            print(f"[main] Progress: {i+1}/{len(cases)} cases | {elapsed:.0f}s elapsed | ETA {remaining:.0f}s")

    total_elapsed = time.time() - t_all
    print(f"\n[main] Processed {len(cases)} cases in {total_elapsed:.1f}s")

    # Write output.csv
    results.sort(key=lambda r: case_sort_key(r["case_id"]))
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for r in results:
            writer.writerow([r["case_id"], r["deletion_status"], r["steps_json"]])

    print(f"[main] Written {len(results)} rows to {output_path}")

    # Print quick status breakdown
    from collections import Counter
    status_counts = Counter(r["deletion_status"] for r in results)
    print(f"[main] Status breakdown: {dict(status_counts)}")

    return results


if __name__ == "__main__":
    main()
