import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict

STATE_FILE = "rss_state.json"


# ====== State Management ======

def _load_state() -> Dict[str, str]:
    """Load the entire RSS state JSON (feed name -> timestamp)."""
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_state(data: Dict[str, str]) -> None:
    """Save the entire RSS state JSON."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_last_run_time(feed_name: str) -> Optional[datetime]:
    """Load last run time for a specific feed."""
    data = _load_state()
    gmt_str = data.get(feed_name)
    if not gmt_str:
        return None
    try:
        return datetime.strptime(gmt_str, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def save_last_run_time(feed_name: str, dt: datetime) -> None:
    """Save last run time for a specific feed."""
    data = _load_state()
    gmt_str = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    data[feed_name] = gmt_str
    _save_state(data)


# ====== Relevance Helper ======

def extract_score_reason(result):
    """Extract score (int) and reasoning (str) from an LLM structured output."""
    if hasattr(result, "score"):
        try:
            return int(result.score), getattr(result, "reasoning", "")
        except Exception:
            return None, getattr(result, "reasoning", "")
    try:
        score = result.get("score")  # type: ignore
        reason = result.get("reasoning")  # type: ignore
        return int(score) if score is not None else None, reason
    except Exception:
        return None, None
