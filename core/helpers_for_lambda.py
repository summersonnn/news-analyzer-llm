# Use this for AWS Lambda!

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict
import boto3
from botocore.exceptions import ClientError

# ====== Configuration ======
BUCKET_NAME = "news-analyzer-timelog"
STATE_FILE_KEY = "rss_state.json"
LOCAL_FALLBACK_PATH = "/tmp/rss_state.json"

s3 = boto3.client("s3")


# ====== State Management ======

def _load_state() -> Dict[str, str]:
    """Load the entire RSS state JSON (feed name -> timestamp) from S3 or fallback."""
    # Try loading from S3
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=STATE_FILE_KEY)
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)
        print(f"[INFO] Loaded state from s3://{BUCKET_NAME}/{STATE_FILE_KEY}")
        return data
    except s3.exceptions.NoSuchKey:
        print("[INFO] State file not found in S3 — starting fresh.")
        return {}
    except ClientError as e:
        print(f"[WARN] Could not load state from S3: {e}")

    # Fallback to local /tmp if available
    if os.path.exists(LOCAL_FALLBACK_PATH):
        try:
            with open(LOCAL_FALLBACK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load fallback state: {e}")

    return {}


def _save_state(data: Dict[str, str]) -> None:
    """Save the entire RSS state JSON to S3 (with local /tmp fallback)."""
    json_data = json.dumps(data, ensure_ascii=False, indent=2)

    # Try saving to S3
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=STATE_FILE_KEY,
            Body=json_data.encode("utf-8"),
            ContentType="application/json"
        )
        print(f"[INFO] Saved state to s3://{BUCKET_NAME}/{STATE_FILE_KEY}")
        return
    except ClientError as e:
        print(f"[ERROR] Failed to save state to S3: {e}")

    # Fallback to /tmp
    try:
        with open(LOCAL_FALLBACK_PATH, "w", encoding="utf-8") as f:
            f.write(json_data)
        print(f"[INFO] Saved fallback state to {LOCAL_FALLBACK_PATH}")
    except Exception as err:
        print(f"[ERROR] Could not save fallback state: {err}")


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
