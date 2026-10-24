import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pytest

from audit.loaders import norm_email, norm_phone, norm_name, email_hash
from audit.models import EvidenceFile, Observation
from audit.extract.text_extractor import extract_text_evidence
from audit.extract.json_extractor import extract_json_evidence
from audit.extract.log_extractor import extract_log_evidence
from audit.extract.sql_extractor import extract_sql_evidence

def test_norm_email():
    assert norm_email("  Amina.ElMasri+tag@Gmail.COM  ") == "amina.elmasri+tag@gmail.com"
    assert norm_email("Decoy.User@example.com") == "decoy.user@example.com"
    assert norm_email("") == ""
    assert norm_email(None) == ""

def test_norm_phone():
    assert norm_phone(" +1 (555) 234-5678 ") == "+15552345678"
    assert norm_phone(" 020 7946 0991 ") == "02079460991"
    assert norm_phone("+34 628 491 736") == "+34628491736"
    assert norm_phone("") == ""
    assert norm_phone(None) == ""

def test_norm_name_and_hash():
    assert norm_name("  Jane   DOE  ") == "jane doe"
    assert len(email_hash("user@example.com")) == 64
    assert email_hash("USER@Example.COM") == email_hash("user@example.com")

def test_mixed_case_email_in_handover_txt(tmp_path: Path):
    txt_file = tmp_path / "handover_test.txt"
    content = (
        "# Snapshot: 2026-09-15T12:00:00Z\n"
        "2026-09-15T10:30:00Z | account_service | account_999 | ACCOUNT_PROFILE | SUCCESS | John.Doe+123@Example.COM\n"
    )
    txt_file.write_text(content, encoding="utf-8")
    
    ev_file = EvidenceFile(
        file_id="evidence_test_txt",
        file_path=str(txt_file),
        origin="customer_account_service",
        captured_at=datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    obs_list = extract_text_evidence(txt_file, ev_file)
    assert len(obs_list) == 1
    obs = obs_list[0]
    assert obs.resource_id == "account_999"
    assert obs.system_hint == "account_service"
    assert "john.doe+123@example.com" in obs.identifiers
    # Ensure raw uppercase is NOT in identifiers
    assert "John.Doe+123@Example.COM" not in obs.identifiers

def test_json_nested_document_extraction(tmp_path: Path):
    json_file = tmp_path / "bundle_test.json"
    data = {
        "snapshot_metadata": {
            "origin": "records_service",
            "timestamp": "2026-09-17T12:00:00Z"
        },
        "nested_records": [
            {
                "record_id": "support_doc_001",
                "owner": "user_456",
                "customer_email": "Customer.One@domain.com",
                "status": "EXPOSED",
                "details": {
                    "nested_attachment": "passport.pdf"
                }
            }
        ]
    }
    import json
    json_file.write_text(json.dumps(data), encoding="utf-8")
    
    ev_file = EvidenceFile(
        file_id="evidence_test_json",
        file_path=str(json_file),
        origin="records_service",
        captured_at=datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    obs_list = extract_json_evidence(json_file, ev_file)
    assert len(obs_list) >= 1
    matched = [o for o in obs_list if o.resource_id == "support_doc_001"]
    assert len(matched) == 1
    obs = matched[0]
    assert obs.status == "PRESENT"  # EXPOSED maps to PRESENT
    assert "customer.one@domain.com" in obs.identifiers
    assert "user_456" in obs.identifiers

def test_log_trace_correlation_timeout_and_recovery(tmp_path: Path):
    log_file = tmp_path / "trace_test.log"
    # worker_99 starts query, then times out
    # worker_100 retries same trace_id tr_555 and completes with rows=0
    lines = [
        '2026-09-18T10:00:00Z [INFO] [account_service] [tr_555] query_start: worker="worker_99" resource_id="account_888" email="User888@test.com"',
        '2026-09-18T10:00:05Z [WARN] [account_service] [tr_555] query_timeout: worker="worker_99" elapsed_ms=5000',
        '2026-09-18T10:00:06Z [INFO] [account_service] [tr_555] query_retry: worker="worker_100" resource_id="account_888"',
        '2026-09-18T10:00:07Z [INFO] [account_service] [tr_555] query_completed: worker="worker_100" rows=0 http_status=200',
    ]
    log_file.write_text("\n".join(lines), encoding="utf-8")
    
    ev_file = EvidenceFile(
        file_id="evidence_test_log",
        file_path=str(log_file),
        origin="observability",
        captured_at=datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    obs_list = extract_log_evidence(log_file, ev_file)
    assert len(obs_list) == 1
    obs = obs_list[0]
    assert obs.resource_id == "account_888"
    assert obs.status == "ABSENT"  # rows=0 maps to ABSENT
    assert "user888@test.com" in obs.identifiers

def test_sql_snapshot_extraction(tmp_path: Path):
    sql_file = tmp_path / "snapshot_test.sql"
    sql_text = """
    -- Captured at: 2026-09-20T12:00:00Z
    CREATE TABLE customer_profiles (
        resource_id TEXT PRIMARY KEY,
        user_id TEXT,
        email TEXT,
        updated_at TEXT
    );
    INSERT INTO customer_profiles VALUES ('account_101', 'user_101', 'user101@example.com', '2026-09-20T11:00:00Z');
    -- snapshot_completed_at=2026-09-20T12:05:00Z
    """
    sql_file.write_text(sql_text, encoding="utf-8")
    
    ev_file = EvidenceFile(
        file_id="evidence_test_sql",
        file_path=str(sql_file),
        origin="customer_db",
        captured_at=datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc),
    )
    
    obs_list = extract_sql_evidence(sql_file, ev_file)
    assert len(obs_list) == 1
    obs = obs_list[0]
    assert obs.resource_id == "account_101"
    assert obs.status == "PRESENT"
    assert "user101@example.com" in obs.identifiers
