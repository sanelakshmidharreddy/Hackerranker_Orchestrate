"""
Evaluator for deletion audit agent output vs sample_output.csv.

Metrics computed:
1. Case status accuracy: deletion_status match (COMPLETE / INCOMPLETE / NOT_APPLICABLE)
2. Step count accuracy: exact count of steps in steps_json
3. Field-level step accuracy:
   - phase, system_id, resource_id, operation, state, evidence_id
4. Sequence accuracy: exact step sequence matching
"""

import csv
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DATASET_DIR = _REPO_ROOT / "dataset"


def load_csv(path: Path):
    rows = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cid = r["case_id"].strip()
            rows[cid] = {
                "status": r["deletion_status"].strip(),
                "steps": json.loads(r["steps_json"]),
            }
    return rows


def evaluate(pred_path: Path, truth_path: Path, verbose: bool = False):
    preds = load_csv(pred_path)
    truth = load_csv(truth_path)

    total_cases = len(truth)
    correct_status = 0
    correct_step_count = 0
    exact_sequence_match = 0

    total_truth_steps = 0
    matched_steps = 0
    field_matches = {
        "phase": 0,
        "system_id": 0,
        "resource_id": 0,
        "operation": 0,
        "state": 0,
        "evidence_id": 0,
    }

    mismatches = []

    for cid, t_data in sorted(truth.items()):
        p_data = preds.get(cid)
        if not p_data:
            mismatches.append(f"[{cid}] MISSING in predictions")
            continue

        status_match = (p_data["status"] == t_data["status"])
        if status_match:
            correct_status += 1
        else:
            mismatches.append(f"[{cid}] STATUS MISMATCH: pred={p_data['status']} vs truth={t_data['status']}")

        t_steps = t_data["steps"]
        p_steps = p_data["steps"]

        if len(t_steps) == len(p_steps):
            correct_step_count += 1

        # Check step by step
        total_truth_steps += len(t_steps)
        seq_ok = True
        if len(t_steps) != len(p_steps):
            seq_ok = False

        for i, ts in enumerate(t_steps):
            if i < len(p_steps):
                ps = p_steps[i]
                step_exact = True
                for field in ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]:
                    if ps.get(field) == ts.get(field):
                        field_matches[field] += 1
                    else:
                        step_exact = False
                if step_exact:
                    matched_steps += 1
                else:
                    seq_ok = False
            else:
                seq_ok = False

        if seq_ok and len(t_steps) > 0:
            exact_sequence_match += 1

    print("=" * 60)
    print("DELETION AUDIT EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Cases Evaluated: {total_cases}")
    print(f"Case Status Accuracy : {correct_status}/{total_cases} ({correct_status/total_cases*100:.1f}%)")
    print(f"Step Count Accuracy  : {correct_step_count}/{total_cases} ({correct_step_count/total_cases*100:.1f}%)")
    print(f"Exact Sequence Match : {exact_sequence_match}/{total_cases} ({exact_sequence_match/total_cases*100:.1f}%)")
    print("-" * 60)
    print(f"Total Truth Steps    : {total_truth_steps}")
    print(f"Exact Matched Steps  : {matched_steps}/{total_truth_steps} ({matched_steps/total_truth_steps*100:.1f}%)")
    print("Field-level Accuracy :")
    for f, count in field_matches.items():
        pct = (count / total_truth_steps * 100) if total_truth_steps > 0 else 0
        print(f"  - {f:12s}: {count}/{total_truth_steps} ({pct:.1f}%)")
    print("-" * 60)
    if mismatches:
        print(f"Mismatches ({len(mismatches)}):")
        for m in mismatches[:15]:
            print(" ", m)
        if len(mismatches) > 15:
            print(f"  ... and {len(mismatches)-15} more.")
    print("=" * 60)

    return {
        "status_acc": correct_status / total_cases,
        "seq_acc": exact_sequence_match / total_cases,
        "matched_steps_pct": matched_steps / total_truth_steps,
    }


if __name__ == "__main__":
    pred = Path(sys.argv[1]) if len(sys.argv) > 1 else (_REPO_ROOT / "output.csv")
    truth = Path(sys.argv[2]) if len(sys.argv) > 2 else (_DATASET_DIR / "sample_output.csv")
    evaluate(pred, truth)
