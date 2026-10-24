import os
from pathlib import Path
from typing import Dict, Optional

from .config import DATASET_DIR, EVIDENCE_DIR
from .extract.activity_extractor import extract_activity_observations
from .extract.json_extractor import extract_json_evidence
from .extract.log_extractor import extract_log_evidence
from .extract.pdf_extractor import extract_pdf_evidence
from .extract.image_extractor import extract_image_evidence
from .extract.sql_extractor import extract_sql_evidence
from .extract.text_extractor import extract_text_evidence
from .loaders import load_evidence_manifest, load_system_activity
from .models import EvidenceFile
from .store import ObservationStore

def build_observation_store(
    dataset_dir: Optional[Path] = None,
    include_activity: bool = True,
    include_multimodal: bool = True,
    custom_manifest: Optional[Dict[str, EvidenceFile]] = None,
) -> ObservationStore:
    """Ingest all SQL, JSON, TXT, LOG, PDF, image evidence files and activity log into ObservationStore."""
    if dataset_dir is None:
        dataset_dir = DATASET_DIR

    store = ObservationStore()

    manifest_path = dataset_dir / "evidence_files.csv"
    manifest = custom_manifest or (load_evidence_manifest(manifest_path) if manifest_path.exists() else {})

    # Map file relative path to EvidenceFile
    path_to_ev: Dict[str, EvidenceFile] = {}
    for ef in manifest.values():
        norm_p = ef.file_path.replace("\\", "/").lstrip("/")
        path_to_ev[norm_p] = ef

    ev_dir = dataset_dir / "evidence"

    # 1. SQL snapshots
    sql_files = sorted((ev_dir / "databases").glob("*.sql"))
    for sf in sql_files:
        rel = f"databases/{sf.name}"
        ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
        obs_list = extract_sql_evidence(sf, ev)
        store.add_many(obs_list)

    # 2. JSON records
    json_files = sorted((ev_dir / "records").glob("*.json"))
    for jf in json_files:
        rel = f"records/{jf.name}"
        ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
        obs_list = extract_json_evidence(jf, ev)
        store.add_many(obs_list)

    # 3. TXT handover records
    txt_files = sorted((ev_dir / "records").glob("*.txt"))
    for tf in txt_files:
        rel = f"records/{tf.name}"
        ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
        obs_list = extract_text_evidence(tf, ev)
        store.add_many(obs_list)

    # 4. Logs
    log_files = sorted((ev_dir / "logs").glob("*.log"))
    for lf in log_files:
        rel = f"logs/{lf.name}"
        ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
        obs_list = extract_log_evidence(lf, ev)
        store.add_many(obs_list)

    # 5. Activity log
    if include_activity:
        act_path = dataset_dir / "system_activity.csv"
        if act_path.exists():
            activities = load_system_activity(act_path)
            act_obs = extract_activity_observations(activities)
            store.add_many(act_obs)

    # 6. PDF documents
    if include_multimodal:
        pdf_files = sorted((ev_dir / "documents").glob("*.pdf"))
        for pf in pdf_files:
            rel = f"documents/{pf.name}"
            ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
            obs_list = extract_pdf_evidence(pf, ev)
            store.add_many(obs_list)

    # 7. Images (screenshots)
    if include_multimodal:
        img_files = sorted((ev_dir / "images").glob("*.png"))
        for imf in img_files:
            rel = f"images/{imf.name}"
            ev = path_to_ev.get(f"evidence/{rel}") or path_to_ev.get(rel)
            obs_list = extract_image_evidence(imf, ev)
            store.add_many(obs_list)

    # 8. User identities and audit log
    from .extract.audit_extractor import extract_user_audit_observations, extract_user_identity_observations
    from .loaders import load_user_audit_log, load_user_identities

    ident_path = dataset_dir / "user_identities.csv"
    if ident_path.exists():
        identities = load_user_identities(ident_path)
        ident_obs = extract_user_identity_observations(identities)
        store.add_many(ident_obs)

    audit_path = dataset_dir / "user_audit_log.csv"
    if audit_path.exists():
        audit_rows = load_user_audit_log(audit_path)
        audit_obs = extract_user_audit_observations(audit_rows)
        store.add_many(audit_obs)

    store.finalize()
    return store
