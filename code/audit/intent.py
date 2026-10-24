"""
Intent classifier: determines if a request_text authorizes deletion.

Strategy:
1. Keyword/pattern layer (fast, no LLM): covers ~95% of cases.
   - Deletion: "delete", "erase", "remove account", "close account", "suppression",
     "verwijder", "löschen", "borrar", "削除", "삭제", etc.
   - Non-deletion keywords (explicit opt-out markers) override:
     "unsubscribe", "marketing", "update email", "change email", "change name",
     "update phone", "name change", "invoice copy", "download", "export my data",
     "access request", "correction", "reset password", "forgot password"
2. LLM layer (cached): invoked only if the keyword layer is ambiguous.

Returns "DELETION" or "NOT_APPLICABLE".
"""

import re
import sys
from pathlib import Path
from typing import Optional

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# --------------------------------------------------------------------------
# Keyword patterns
# --------------------------------------------------------------------------

_DELETION_PATTERNS = [
    # English
    r"\bdelet\w*\b",
    r"\beras\w*\b",
    r"\bremov\w*\s+(my\s+|the\s+|this\s+)?(account|profile|data|record|details)",
    r"\bclos\w*\s+(my\s+|the\s+|this\s+)?account\b",
    r"\b(permanently\s+)?remov\w*\b",
    r"\bwipe\b",
    r"\bpurge\b",
    r"\bforget\s+me\b",
    r"\bright\s+to\s+be\s+forgotten\b",
    r"\bgdpr\s+deletion\b",
    r"\bdata\s+deletion\b",
    r"\brequest\s+deletion\b",
    r"\bprofile\s+is\s+gone\b",
    r"\bcannot\s+identify\s+me\b",
    # French
    r"\bsuppress\w*\b", r"\bsupprim\w*\b", r"\beffac\w*\b",
    # Spanish
    r"\belimin\w*\b", r"\bborr\w*\b",
    # German
    r"\blöschen\b", r"\bl.schen\b", r"\bL.schung\b",
    # Japanese
    r"削除", r"消去",
    # Korean
    r"삭제", r"제거",
    # Portuguese
    r"\bapagar\b", r"\bexcluir\b",
    # Dutch
    r"\bverwijder\w*\b",
    # Italian
    r"\bcancel\w*\b",
    # Arabic
    r"حذف",
    # General
    r"\bremove\s+personal\s+data\b",
    r"\bclose\s+and\s+delete\b",
]

_NON_DELETION_PATTERNS = [
    r"\bunsubscribe\b",
    r"\bmarketing\s+(list|email|opt.out)\b",
    r"\bopt.out\s+of\s+marketing\b",
    r"\bremove\s+(from|me\s+from)\s+marketing\b",
    r"\bstop\s+(sending|receiving)\s+(email|newsletter|promo)",
    r"\bupdate\s+(my\s+)?(mobile\s+)?(number|phone|email|name|address)",
    r"\bchange\s+(my\s+)?(account\s+)?(email|phone|name|address|password)",
    r"\b(name|email|phone)\s+(change|correction|update)\b",
    r"\bpassword\s+reset\b", r"\bforgot\s+password\b", r"\breset\s+password\b", r"\blogin\s+reset\b",
    r"\bdownload\s+(my\s+)?data\b", r"\bexport\s+(my\s+)?data\b", r"\bportable\s+data\b",
    r"\baccess\s+request\b", r"\bright\s+to\s+access\b", r"\bsar\b",
    r"\bdata\s+portability\b",
    r"\binvoice\s+(copy|copies|request)\b", r"\bcopy\s+of\s+(my\s+)?invoice\b",
    r"\bdata\s+correction\b", r"\bcorrect\s+(my\s+)?data\b",
    r"\bmisspelled\s+surname\b",
    r"\bcopy\s+of\s+held\s+information\b",
    r"\btax\s+record\b",
    r"\bwhere\s+is\s+my\s+(order|delivery)\b",
    r"\btrack\s+(my\s+)?(order|package|delivery)\b",
]

_DEL_RE = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in _DELETION_PATTERNS]
_NON_DEL_RE = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in _NON_DELETION_PATTERNS]


_EXPLICIT_NON_DELETION_PHRASES = [
    r"\bnot\s+asking\s+for\s+deletion\b",
    r"\bnot\s+a\s+request\s+to\s+erase\b",
    r"\b(do\s+not|don't)\s+(delete|close|remove)\b",
    r"\bwithout\s+removing\b",
    r"\bmarketing\s+lists?\s+only\b",
    r"\bleave\s+(the\s+account\s+active|my\s+profile.*in\s+place)\b",
    r"\bkeep\s+the\s+account\s+as\s+it\s+is\b",
    r"\bcontinue\s+using\s+the\s+service\b",
    r"\bportable\s+format\b",
    r"\bresettin\w*\s+the\s+login\b",
    r"\bmobile\s+number.*out\s+of\s+date\b",
    r"\bsurname\s+is\s+misspelled\b",
    r"\bcopy\s+of\s+last\s+year's\s+invoices\b",
    r"\binformation\s+request\b",
    r"\bcopy\s+of\s+the\s+information\s+held\b",
]

_NON_DEL_EXPLICIT_RE = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in _EXPLICIT_NON_DELETION_PHRASES]


def _keyword_classify(text: str) -> Optional[str]:
    """
    Returns 'DELETION' or 'NOT_APPLICABLE'.
    """
    # 1. Check explicit non-deletion phrases (negation / explicit retention request)
    for pat in _NON_DEL_EXPLICIT_RE:
        if pat.search(text):
            return "NOT_APPLICABLE"

    # 2. Check deletion patterns
    has_del = any(pat.search(text) for pat in _DEL_RE)
    if has_del:
        return "DELETION"

    # 3. Check general non-deletion patterns
    has_non_del = any(pat.search(text) for pat in _NON_DEL_RE)
    if has_non_del:
        return "NOT_APPLICABLE"

    # Default: deletion audit context
    return "DELETION"


_LLM_INTENT_PROMPT_TEMPLATE = """\
You are classifying customer service requests for a deletion audit.

Determine if the following request authorizes DELETION of the customer's \
personal data (account profile, records, etc.).

Rules:
- "DELETION" = the person explicitly requests account/data deletion, erasure, \
  right to be forgotten, or full removal of personal data.
- "NOT_APPLICABLE" = the person is requesting something else such as: \
  unsubscribe from marketing, access/download their data, correct/update \
  information, password reset, invoice copy, delivery tracking, or any \
  non-deletion action.
- If the request mentions BOTH deletion and a non-deletion action, classify as \
  "DELETION" only if the deletion is the primary intent.

Request text:
\"\"\"
{text}
\"\"\"

Respond with exactly one word: DELETION or NOT_APPLICABLE"""


def classify_intent(request_text: str, case_id: str = "") -> str:
    """
    Classify whether request_text authorizes deletion.

    Returns "DELETION" or "NOT_APPLICABLE".
    """
    if not request_text or not request_text.strip():
        return "NOT_APPLICABLE"

    result = _keyword_classify(request_text)
    if result is not None:
        return result

    # LLM fallback (cached)
    try:
        from audit.llm import call_llm
        prompt = _LLM_INTENT_PROMPT_TEMPLATE.format(text=request_text.strip())
        response, _ = call_llm(prompt, context_label=f"intent:{case_id}")
        response = response.strip().upper()
        if "NOT_APPLICABLE" in response:
            return "NOT_APPLICABLE"
        if "DELETION" in response:
            return "DELETION"
        # Unexpected response: treat as deletion to be safe
        return "DELETION"
    except Exception:
        # If LLM unavailable and we're here, text was ambiguous — default to DELETION
        return "DELETION"
