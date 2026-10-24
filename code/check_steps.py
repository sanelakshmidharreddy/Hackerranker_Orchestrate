import sys
sys.path.insert(0, "code")
from audit.loaders import *
from audit.identity import resolve_identity
from audit.ingest import build_observation_store
from pathlib import Path

ds = Path("dataset")
cases = load_deletion_requests(ds / "sample_deletion_requests.csv")
users = load_user_identities(ds / "user_identities.csv")
audit_log = load_user_audit_log(ds / "user_audit_log.csv")

store = build_observation_store(ds, include_multimodal=False)

# case_01: audit_at=2026-09-03 so evidence_01(09-15) is future, evidence_05(09-21) is future, evidence_07(09-13) is future
# The sample truth says VERIFY_RECORD_ABSENT for account_001 with no evidence_id listed
# Let's look at what evidence is <= audit_at for case_01
for cid in ["case_01", "case_02", "case_04"]:
    c = next(x for x in cases if x.case_id == cid)
    ident = resolve_identity(case_email=c.email, audit_at=c.audit_at,
                             identity_rows=users, audit_log_rows=audit_log)
    print(f"\n{cid} audit_at={c.audit_at} email={c.email} user_id={ident.user_ids}")
    
    # Find all obs at or before audit_at
    obs = store.get_for_identifiers(ident.all_identifiers, up_to=c.audit_at)
    print(f"  Obs count (before audit_at): {len(obs)}")
    for o in obs:
        ev_ref = o.source_id
        print(f"    rid={o.resource_id} src={ev_ref} cit={o.citable_at} obs={o.observed_at} status={o.status}")
