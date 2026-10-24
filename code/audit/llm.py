"""
LLM module: cached, deterministic (temperature=0) Gemini calls.

- Cache key = sha256(model + prompt_text + base64_of_any_images)
- Cache location = code/cache/llm/
- Token ledger written to code/cache/llm/usage_ledger.jsonl
- Retry: exponential back-off up to 3 attempts, 60-second timeout per call
"""

import base64
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure code/ is on sys.path
_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from config import CACHE_DIR, DEFAULT_EXTRACTION_MODEL, DEFAULT_TEMPERATURE

# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------
_LLM_CACHE_DIR = CACHE_DIR / "llm"
_LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_USAGE_LEDGER_PATH = _LLM_CACHE_DIR / "usage_ledger.jsonl"


def _cache_key(model: str, prompt: str, image_paths: Optional[List[Path]] = None) -> str:
    """Compute stable SHA-256 cache key from model + prompt + image bytes."""
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(b"\x00")
    h.update(prompt.encode("utf-8"))
    if image_paths:
        for p in sorted(image_paths):
            h.update(b"\x00")
            h.update(str(p).encode("utf-8"))
            try:
                h.update(p.read_bytes())
            except Exception:
                pass
    return h.hexdigest()


def _read_cache(key: str) -> Optional[Dict[str, Any]]:
    path = _LLM_CACHE_DIR / f"{key}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _write_cache(key: str, data: Dict[str, Any]) -> None:
    path = _LLM_CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_ledger(entry: Dict[str, Any]) -> None:
    try:
        with open(_USAGE_LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main LLM call (with retry + caching)
# ---------------------------------------------------------------------------

def call_llm(
    prompt: str,
    model: str = DEFAULT_EXTRACTION_MODEL,
    image_paths: Optional[List[Path]] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_retries: int = 3,
    context_label: str = "",
) -> Tuple[str, Dict[str, Any]]:
    """
    Call Gemini model with caching.

    Returns:
        (text_response, usage_dict)
    """
    key = _cache_key(model, prompt, image_paths)
    cached = _read_cache(key)
    if cached:
        return cached["text"], cached["usage"]

    # Late import to avoid loading google.genai at import time when cache hits
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError as e:
        raise RuntimeError(f"google-genai not installed: {e}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Try dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv(_CODE_DIR.parent / ".env")
            api_key = os.environ.get("GEMINI_API_KEY")
        except Exception:
            pass

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    # Build contents
    contents: List[Any] = []
    if image_paths:
        for img_path in image_paths:
            try:
                img_bytes = img_path.read_bytes()
                suffix = img_path.suffix.lower()
                mime = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }.get(suffix, "image/png")
                contents.append(
                    genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
                )
            except Exception as exc:
                print(f"[LLM] Warning: cannot read image {img_path}: {exc}", file=sys.stderr)
    contents.append(prompt)

    # Retry loop
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )
            text = response.text or ""
            usage: Dict[str, Any] = {}
            try:
                u = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(u, "prompt_token_count", 0) or 0,
                    "completion_tokens": getattr(u, "candidates_token_count", 0) or 0,
                    "total_tokens": getattr(u, "total_token_count", 0) or 0,
                }
            except Exception:
                pass

            entry = {
                "key": key,
                "model": model,
                "context_label": context_label,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
                "usage": usage,
                "text": text,
            }
            _write_cache(key, entry)
            _append_ledger({k: v for k, v in entry.items() if k != "text"})
            return text, usage

        except Exception as exc:
            last_exc = exc
            wait = 2 ** attempt * 5  # 5s, 10s, 20s
            print(
                f"[LLM] Attempt {attempt + 1}/{max_retries} failed: {exc}. "
                f"Retrying in {wait}s…",
                file=sys.stderr,
            )
            time.sleep(wait)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_exc}")


# ---------------------------------------------------------------------------
# Convenience: load usage summary from ledger
# ---------------------------------------------------------------------------

def load_usage_summary() -> Dict[str, Any]:
    """Aggregate token counts and cost estimate from the ledger."""
    total_calls = 0
    cache_hits = 0
    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    per_model: Dict[str, Dict[str, int]] = {}

    if _USAGE_LEDGER_PATH.exists():
        with open(_USAGE_LEDGER_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    total_calls += 1
                    if entry.get("cached"):
                        cache_hits += 1
                    u = entry.get("usage", {})
                    pt = u.get("prompt_tokens", 0) or 0
                    ct = u.get("completion_tokens", 0) or 0
                    tt = u.get("total_tokens", 0) or 0
                    total_prompt += pt
                    total_completion += ct
                    total_tokens += tt
                    mdl = entry.get("model", "unknown")
                    if mdl not in per_model:
                        per_model[mdl] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    per_model[mdl]["calls"] += 1
                    per_model[mdl]["prompt_tokens"] += pt
                    per_model[mdl]["completion_tokens"] += ct
                    per_model[mdl]["total_tokens"] += tt
                except Exception:
                    pass

    return {
        "total_calls": total_calls,
        "cache_hits": cache_hits,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_tokens,
        "per_model": per_model,
    }
