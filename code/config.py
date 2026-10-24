import os
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_DIR = DATASET_DIR / "evidence"
CODE_DIR = REPO_ROOT / "code"
PROMPTS_DIR = CODE_DIR / "prompts"
CACHE_DIR = CODE_DIR / "cache"
EVALUATION_DIR = CODE_DIR / "evaluation"

# Models and settings
DEFAULT_REASONING_MODEL = "gemini-3.8-flash"
DEFAULT_VISION_MODEL = "gemini-3.8-flash"
DEFAULT_EXTRACTION_MODEL = "gemini-3.8-flash"
DEFAULT_TEMPERATURE = 0.0

# Operations Vocabulary (Closed 15-operation vocabulary from Problem Statement Appendix A)
OP_ORDER = [
    "REPORT_REMAINING_RECORD",
    "REPORT_EXPOSED_PII",
    "REPORT_ACTIVE_DATA_FLOW",
    "REPORT_RESTORE_RISK",
    "DISABLE_DATA_FLOW",
    "BLOCK_RESTORE",
    "DELETE_RECORD",
    "REDACT_RECORD",
    "ANONYMIZE_RECORD",
    "VERIFY_RECORD_ABSENT",
    "VERIFY_RECORD_PRESENT",
    "VERIFY_RECORD_REDACTED",
    "VERIFY_RECORD_ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED",
    "VERIFY_RESTORE_BLOCKED",
]

PHASE_ORDER = {
    "FINDING": 0,
    "REMEDIATION": 1,
    "VERIFICATION": 2,
}

OPERATION_STATE_MAP = {
    "REPORT_REMAINING_RECORD": "PRESENT",
    "REPORT_EXPOSED_PII": "PRESENT",
    "REPORT_ACTIVE_DATA_FLOW": "ACTIVE",
    "REPORT_RESTORE_RISK": "ACTIVE",
    "DISABLE_DATA_FLOW": "DISABLED",
    "BLOCK_RESTORE": "BLOCKED",
    "DELETE_RECORD": "ABSENT",
    "REDACT_RECORD": "REDACTED",
    "ANONYMIZE_RECORD": "ANONYMIZED",
    "VERIFY_RECORD_ABSENT": "ABSENT",
    "VERIFY_RECORD_PRESENT": "PRESENT",
    "VERIFY_RECORD_REDACTED": "REDACTED",
    "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
    "VERIFY_DATA_FLOW_DISABLED": "DISABLED",
    "VERIFY_RESTORE_BLOCKED": "BLOCKED",
}

OPERATION_PHASE_MAP = {
    "REPORT_REMAINING_RECORD": "FINDING",
    "REPORT_EXPOSED_PII": "FINDING",
    "REPORT_ACTIVE_DATA_FLOW": "FINDING",
    "REPORT_RESTORE_RISK": "FINDING",
    "DISABLE_DATA_FLOW": "REMEDIATION",
    "BLOCK_RESTORE": "REMEDIATION",
    "DELETE_RECORD": "REMEDIATION",
    "REDACT_RECORD": "REMEDIATION",
    "ANONYMIZE_RECORD": "REMEDIATION",
    "VERIFY_RECORD_ABSENT": "VERIFICATION",
    "VERIFY_RECORD_PRESENT": "VERIFICATION",
    "VERIFY_RECORD_REDACTED": "VERIFICATION",
    "VERIFY_RECORD_ANONYMIZED": "VERIFICATION",
    "VERIFY_DATA_FLOW_DISABLED": "VERIFICATION",
    "VERIFY_RESTORE_BLOCKED": "VERIFICATION",
}

# Prefix to default system and category mapping
PREFIX_SYSTEM_CATEGORY = {
    "account_": ("account_service", "USER_PROFILE"),
    "search_": ("search_service", "SEARCH_INDEX_ENTRY"),
    "support_": ("support_platform", "SUPPORT_MESSAGE"),
    "analytics_": ("analytics_platform", "ANALYTICS_PROFILE"),
    "audit_record_": ("security_service", "SECURITY_AUDIT_LOG"),
    "data_flow_": ("integration_service", "DATA_FLOW"),
    "backup_": ("backup_service", "BACKUP_ARCHIVE"),
    "export_": ("export_service", "USER_EXPORT"),
    "tombstone_": ("identity_service", "ACCOUNT_TOMBSTONE"),
    "cache_": ("cache_service", "CACHE_ENTRY"),
    "email_": ("email_delivery_service", "EMAIL_DELIVERY_LOG"),
    "marketing_": ("marketing_service", "MARKETING_PROFILE"),
    "legal_": ("legal_service", "LEGAL_HOLD_RECORD"),
}
