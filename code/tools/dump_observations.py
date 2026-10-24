import argparse
import sys
from collections import Counter
from pathlib import Path

# Force UTF-8 stdout
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "code"))

from audit.ingest import build_observation_store
from audit.loaders import norm_email

def main():
    parser = argparse.ArgumentParser(description="Dump chronological observations for a resource or email.")
    parser.add_argument("--resource", type=str, help="Resource ID (e.g. account_005)")
    parser.add_argument("--email", type=str, help="Email address (e.g. amina.elmasri@gmail.com)")
    parser.add_argument("--stats", action="store_true", help="Print mapping statistics and histograms")
    args = parser.parse_args()

    print("Building ObservationStore from dataset evidence...")
    store = build_observation_store()
    all_obs = store.get_all_observations()
    print(f"Total observations ingested: {len(all_obs)}")

    # Compute status histograms
    status_counts = Counter(o.status for o in all_obs)
    claim_counts = Counter(o.is_claim for o in all_obs)
    source_kind_counts = Counter(o.source_kind for o in all_obs)

    print("\n--- Canonical Status Histogram ---")
    for st, c in status_counts.most_common():
        print(f"  {st:20s}: {c}")

    print(f"\n--- Claim Breakdown: is_claim=True: {claim_counts[True]}, is_claim=False: {claim_counts[False]} ---")
    print(f"--- Evidence Source Kinds: {dict(source_kind_counts)} ---")

    unmapped = [o for o in all_obs if o.status in ("UNKNOWN", "UNMAPPED")]
    print(f"\nTotal UNMAPPED / UNKNOWN status observations: {len(unmapped)}")

    if args.resource:
        rid = args.resource.strip()
        print(f"\n================================================================================")
        print(f"TIMELINE FOR RESOURCE: {rid}")
        print(f"================================================================================")
        timeline = store.get_for_resource(rid)
        if not timeline:
            print(f"No observations found for resource '{rid}'.")
        else:
            print(f"{'Time':<24} | {'Source ID':<12} | {'Kind':<8} | {'System':<20} | {'Status':<14} | {'Claim?':<6} | {'Identifiers'}")
            print("-" * 110)
            for o in timeline:
                ts_str = o.observed_at.isoformat()
                src = o.source_id or ""
                kind = o.source_kind
                sys_hint = o.system_hint or ""
                st = o.status
                claim_str = "YES" if o.is_claim else "no"
                idents_str = ", ".join(sorted(o.identifiers))
                print(f"{ts_str:<24} | {src:<12} | {kind:<8} | {sys_hint:<20} | {st:<14} | {claim_str:<6} | {idents_str}")

    if args.email:
        em = norm_email(args.email)
        print(f"\n================================================================================")
        print(f"TIMELINE FOR EMAIL: {em}")
        print(f"================================================================================")
        
        # Collect all linked identifiers from matching observations (e.g. user_id, hash)
        matched_obs = store.get_for_identifier(em)
        all_idents = {em}
        for o in matched_obs:
            all_idents.update(o.identifiers)

        # Pull all observations matching any of these identifiers
        timeline = store.get_for_identifiers(all_idents)
        
        # Also check if any resource_ids belong to this subject
        linked_rids = set()
        for o in timeline:
            if o.resource_id:
                linked_rids.add(o.resource_id)

        # Check deletion worker activities for this user/email around cases if available
        # Add observations for linked resources
        for rid in linked_rids:
            for o in store.get_for_resource(rid):
                if o not in timeline:
                    timeline.append(o)

        timeline.sort(key=lambda o: (o.observed_at, o.source_id))

        if not timeline:
            print(f"No observations found for email '{em}'.")
        else:
            print(f"{'Time':<24} | {'Source ID':<13} | {'Kind':<9} | {'System':<20} | {'Status':<14} | {'Claim?':<6} | {'Resource ID':<18} | {'Identifiers'}")
            print("-" * 135)
            for o in timeline:
                ts_str = o.observed_at.isoformat()
                src = o.source_id or ""
                kind = o.source_kind
                sys_hint = o.system_hint or ""
                st = o.status
                claim_str = "YES" if o.is_claim else "no"
                rid = o.resource_id or ""
                idents_str = ", ".join(sorted(o.identifiers))
                print(f"{ts_str:<24} | {src:<13} | {kind:<9} | {sys_hint:<20} | {st:<14} | {claim_str:<6} | {rid:<18} | {idents_str}")

if __name__ == "__main__":
    main()
