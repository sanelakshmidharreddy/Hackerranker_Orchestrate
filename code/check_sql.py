import sys
sys.path.insert(0, "code")
from audit.extract.sql_extractor import extract_sql_evidence
from audit.loaders import load_evidence_manifest
from pathlib import Path

manifest = load_evidence_manifest("dataset/evidence_files.csv")
ev = manifest["evidence_05"]
obs = extract_sql_evidence(Path("dataset/evidence/databases/customer_data_read_replica_20260921.sql"), ev)

# Check identifiers for key resources
for o in obs:
    if o.resource_id in ("analytics_4440", "account_994", "search_1007", "search_8911"):
        print(f"RID={o.resource_id:20s}  status={o.status:12s}  idents={set(o.identifiers)}")
