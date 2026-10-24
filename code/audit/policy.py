"""
Policy engine: maps (record_type, observation) to the required action
from deletion_rules.csv.

Returns one of: "DELETE", "REDACT", "ANONYMIZE", "RETAIN", "BLOCK"

Notes:
- rule_05 vs rule_06: SUPPORT_MESSAGE (shared conversation) -> REDACT;
  SUPPORT_ATTACHMENT (belongs only to subject) -> DELETE.
- rule_14: BACKUP_ARCHIVE -> RETAIN but block restore (BLOCK_RESTORE remediation).
- rule_15: ACCOUNT_TOMBSTONE -> REDACT (keep user_id, remove name/email/phone/hash).
- SECURITY_AUDIT_LOG and LEGAL_HOLD_RECORD -> RETAIN.
- Unknown/unmapped categories -> DELETE (safest default for personal data).
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Optional

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# --------------------------------------------------------------------------
# Hard-coded policy table (from deletion_rules.csv)
# We load dynamically but keep a fallback hard-coded map.
# --------------------------------------------------------------------------

_CATEGORY_ACTION_MAP: Dict[str, str] = {
    "USER_PROFILE":          "DELETE",   # rule_01
    "SECONDARY_IDENTIFIER":  "DELETE",   # rule_02
    "SEARCH_INDEX_ENTRY":    "DELETE",   # rule_03
    "CACHE_ENTRY":           "DELETE",   # rule_04
    "SUPPORT_MESSAGE":       "REDACT",   # rule_05 (shared conversation)
    "SUPPORT_ATTACHMENT":    "DELETE",   # rule_06 (only belongs to subject)
    "ANALYTICS_PROFILE":     "ANONYMIZE",# rule_07
    "PRODUCT_TELEMETRY":     "ANONYMIZE",# rule_08
    "USER_EXPORT":           "DELETE",   # rule_09
    "MARKETING_PROFILE":     "DELETE",   # rule_10
    "EMAIL_DELIVERY_LOG":    "REDACT",   # rule_11
    "SECURITY_AUDIT_LOG":    "RETAIN",   # rule_12
    "LEGAL_HOLD_RECORD":     "RETAIN",   # rule_13
    "BACKUP_ARCHIVE":        "RETAIN",   # rule_14 (but BLOCK_RESTORE needed)
    "ACCOUNT_TOMBSTONE":     "REDACT",   # rule_15
    "DATA_FLOW":             "DISABLE",  # not in rules, but active flows must be disabled first
    "IDENTITY_AUDIT":        "RETAIN",   # audit trail records are retained
    "DOCUMENT":              "DELETE",   # generic document default
}

# Aliases: different evidence sources may use slightly different record_type names
_CATEGORY_ALIASES: Dict[str, str] = {
    # SQL table name / JSON collection aliases
    "CUSTOMER_PROFILE":          "USER_PROFILE",
    "CUSTOMER_PROFILES":         "USER_PROFILE",
    "ACCOUNT_PROFILE":           "USER_PROFILE",
    "USER_DATA":                 "USER_PROFILE",
    "SEARCH_ENTRY":              "SEARCH_INDEX_ENTRY",
    "SEARCH_INDEX":              "SEARCH_INDEX_ENTRY",
    "ANALYTICS":                 "ANALYTICS_PROFILE",
    "ANALYTICS_RECORD":          "ANALYTICS_PROFILE",
    "SUPPORT_TICKET":            "SUPPORT_MESSAGE",
    "SUPPORT_RECORD":            "SUPPORT_MESSAGE",
    "SUPPORT_ATTACHMENT_RECORD": "SUPPORT_ATTACHMENT",
    "EXPORT_JOB":                "USER_EXPORT",
    "EXPORT_RECORD":             "USER_EXPORT",
    "BACKUP":                    "BACKUP_ARCHIVE",
    "BACKUP_RECORD":             "BACKUP_ARCHIVE",
    "BACKUP_ENTRY":              "BACKUP_ARCHIVE",
    "TOMBSTONE":                 "ACCOUNT_TOMBSTONE",
    "DELETED_ACCOUNT_REFERENCE": "ACCOUNT_TOMBSTONE",
    "EMAIL_LOG":                 "EMAIL_DELIVERY_LOG",
    "MARKETING":                 "MARKETING_PROFILE",
    "INTEGRATION":               "DATA_FLOW",
    "CONNECTOR":                 "DATA_FLOW",
    "SECURITY_LOG":              "SECURITY_AUDIT_LOG",
    "AUDIT_LOG":                 "SECURITY_AUDIT_LOG",
    "AUDIT_RECORD":              "SECURITY_AUDIT_LOG",
    "LEGAL_RECORD":              "LEGAL_HOLD_RECORD",
    "CACHE":                     "CACHE_ENTRY",
}


def _load_rules_from_csv(rules_path: Path) -> Dict[str, str]:
    """Load deletion_rules.csv into a category->action dict."""
    result = {}
    try:
        with open(rules_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cat = (row.get("data_category") or "").strip().upper()
                action = (row.get("required_action") or "").strip().upper()
                if cat and action:
                    result[cat] = action
    except Exception:
        pass
    return result


def load_policy(rules_path: Optional[Path] = None) -> Dict[str, str]:
    """Load policy map, merging CSV rules over built-in fallback."""
    policy = dict(_CATEGORY_ACTION_MAP)
    if rules_path and rules_path.exists():
        csv_rules = _load_rules_from_csv(rules_path)
        policy.update(csv_rules)
    return policy


def canonical_category(record_type: Optional[str]) -> str:
    """Normalize record_type to canonical category key."""
    if not record_type:
        return "USER_PROFILE"
    upper = record_type.strip().upper()
    return _CATEGORY_ALIASES.get(upper, upper)


def required_action(
    record_type: Optional[str],
    policy: Dict[str, str],
    is_shared_conversation: bool = False,
    attachment_only_subject: bool = True,
) -> str:
    """
    Return the required action for a record.

    Special cases:
    - SUPPORT_MESSAGE with is_shared_conversation=True -> REDACT (rule_05)
    - SUPPORT_MESSAGE with is_shared_conversation=False / attachment_only_subject=True -> DELETE (rule_06)
    """
    cat = canonical_category(record_type)

    # rule_05 vs rule_06 distinction
    if cat == "SUPPORT_MESSAGE":
        if is_shared_conversation:
            return "REDACT"
        else:
            return "DELETE"

    action = policy.get(cat, "DELETE")
    return action


def action_to_finding_operation(action: str, status: str) -> Optional[str]:
    """
    Map (required_action, current_status) to the finding operation.

    Returns None if no finding is needed (record is already in the required state).
    """
    if action == "DELETE":
        if status in ("PRESENT",):
            return "REPORT_REMAINING_RECORD"
        if status in ("EXPOSED", "REDACTED") and status != "ABSENT":
            return "REPORT_REMAINING_RECORD"
        return None  # already absent or retained

    if action == "REDACT":
        if status in ("PRESENT",):
            return "REPORT_EXPOSED_PII"
        if status == "REDACTED":
            return None  # already done
        return None

    if action == "ANONYMIZE":
        if status in ("PRESENT",):
            return "REPORT_EXPOSED_PII"
        if status == "ANONYMIZED":
            return None
        return None

    if action == "RETAIN":
        return None  # no finding — this record should stay

    if action == "DISABLE":
        if status == "ACTIVE":
            return "REPORT_ACTIVE_DATA_FLOW"
        return None

    if action == "BLOCK":
        if status in ("RESTORABLE",):
            return "REPORT_RESTORE_RISK"
        return None

    return None


def action_to_remediation_operation(action: str) -> Optional[str]:
    """Map required_action to remediation operation."""
    return {
        "DELETE": "DELETE_RECORD",
        "REDACT": "REDACT_RECORD",
        "ANONYMIZE": "ANONYMIZE_RECORD",
        "DISABLE": "DISABLE_DATA_FLOW",
        "BLOCK": "BLOCK_RESTORE",
    }.get(action)


def action_to_verification_operation(action: str) -> Optional[str]:
    """Map required_action to verification operation."""
    return {
        "DELETE": "VERIFY_RECORD_ABSENT",
        "REDACT": "VERIFY_RECORD_REDACTED",
        "ANONYMIZE": "VERIFY_RECORD_ANONYMIZED",
        "RETAIN": "VERIFY_RECORD_PRESENT",
        "DISABLE": "VERIFY_DATA_FLOW_DISABLED",
        "BLOCK": "VERIFY_RESTORE_BLOCKED",
    }.get(action)
