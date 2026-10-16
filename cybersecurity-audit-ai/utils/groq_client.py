import re
import threading
import time
from collections import deque

from groq import Groq
from config.settings import get_groq_key_info, MODEL_NAME, MAX_TOKENS, TEMPERATURE, TPM_LIMIT

ERROR_PREFIX = "❌ **Agent Error:**"

_WINDOW = 60.0       # Groq enforces tokens-per-minute on a rolling 60s window
_SAFETY = 300        # tokens of headroom under the limit
_usage = deque()     # [timestamp, tokens] entries, shared by every session in this process
_lock = threading.Lock()
_wait_hook = None    # optional callback(seconds_left) so the UI can show a countdown


def set_wait_hook(fn):
    global _wait_hook
    _wait_hook = fn


def is_error(text) -> bool:
    return isinstance(text, str) and text.startswith(ERROR_PREFIX)


def is_fatal(text) -> bool:
    """Errors that retrying cannot fix (bad / missing key)."""
    if not is_error(text):
        return False
    low = text.lower()
    return "error code: 401" in low or "invalid_api_key" in low or "api_key is not set" in low


def get_groq_client():
    api_key, _ = get_groq_key_info()  # resolved at call time, not import time
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add it to Streamlit secrets or .env file.")
    return Groq(api_key=api_key)


def _estimate(*texts) -> int:
    """Conservative token estimate (markdown/tables tokenize worse than prose)."""
    return int(sum(len(t) for t in texts) / 3.2) + 20


def _trim_middle(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.65)
    return text[:head] + "\n...[trimmed to fit the token limit]...\n" + text[-(max_chars - head):]


def _retry_after(msg: str):
    m = re.search(r"try again in\s+([\d.]+)ms", msg)
    if m:
        return float(m.group(1)) / 1000
    m = re.search(r"try again in\s+(?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", msg)
    if not m:
        return None
    h, mi, sec = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + float(sec)


def _countdown(seconds: float):
    for remaining in range(int(seconds) + 1, 0, -1):
        if _wait_hook:
            _wait_hook(remaining)
        time.sleep(1)


def _reserve_budget(requested: int):
    """Block until `requested` tokens fit inside the rolling window; returns a mutable
    entry whose token count is corrected to the real usage after the response."""
    while True:
        with _lock:
            now = time.time()
            while _usage and now - _usage[0][0] >= _WINDOW:
                _usage.popleft()
            used = sum(t for _, t in _usage)
            if not _usage or used + requested <= TPM_LIMIT - _SAFETY:
                entry = [now, requested]
                _usage.append(entry)
                return entry
            wait = _usage[0][0] + _WINDOW - now
        _countdown(max(wait, 0))


def call_agent(system_prompt: str, user_prompt: str, context: str = "", max_tokens: int = None) -> str:
    # `context` is accepted for backward compatibility but ignored: every agent already
    # embeds the previous findings in user_prompt, so sending them twice doubled token use.
    max_out = max_tokens or MAX_TOKENS
    limit = TPM_LIMIT - _SAFETY
    min_out = 700
    try:
        client = get_groq_client()
        for attempt in range(4):
            sys_tokens = _estimate(system_prompt) + 60
            prompt_tokens = sys_tokens + _estimate(user_prompt)
            if prompt_tokens > limit - min_out:  # prompt alone would not fit: trim it
                keep = int((limit - min_out - sys_tokens) * 3.2)
                user_prompt = _trim_middle(user_prompt, max(keep, 1000))
                prompt_tokens = sys_tokens + _estimate(user_prompt)
            out = max(min_out, min(max_out, limit - prompt_tokens))

            system = (
                system_prompt
                + f"\n\nOUTPUT LIMIT: keep the entire response under about {int(out * 0.55)} words. "
                  "Prefer tight tables and bullets over prose, and finish every section."
            )
            entry = _reserve_budget(prompt_tokens + out)
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=out,
                    temperature=TEMPERATURE,
                )
            except Exception as e:
                entry[1] = 0  # failed request: release the reservation
                msg = str(e)
                retryable = "429" in msg or "413" in msg or "rate_limit" in msg.lower()
                if not retryable or attempt == 3:
                    raise
                if "413" in msg or "too large" in msg.lower():
                    user_prompt = _trim_middle(user_prompt, int(len(user_prompt) * 0.7))
                    max_out = max(min_out, int(out * 0.8))
                    continue
                wait = _retry_after(msg)
                if wait is None or wait > 90:  # e.g. daily quota: waiting will not help
                    raise
                _countdown(wait + 1)
                continue

            usage = getattr(response, "usage", None)
            entry[1] = getattr(usage, "total_tokens", None) or (prompt_tokens + out)
            return response.choices[0].message.content

    except Exception as e:
        msg = str(e)
        hint = ""
        low = msg.lower()
        if "error code: 401" in low or "invalid_api_key" in low:
            _, source = get_groq_key_info()
            hint = (f"\n\nThe key was loaded from **{source}** but Groq rejected it. "
                    "Check the sidebar's 🔑 API key status panel.")
        elif "429" in msg or "413" in msg or "rate_limit" in low:
            hint = ("\n\nGroq's free tier limits tokens per minute and per day. "
                    "Wait a minute and run the audit again, or upgrade your Groq plan.")
        return f"{ERROR_PREFIX} {msg}{hint}"
