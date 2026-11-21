import os

import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def _clean(value, limit):
    if isinstance(value, list):
        value = "\n".join(str(v) for v in value)
    text = str(value or "").replace("\\n", "\n")
    return text[:limit]


def send_slack(pod, namespace, reason, d):
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        print("SLACK_WEBHOOK_URL is not set, skipping Slack")
        return False
    text = (
        f":rotating_light: *{pod}* is failing in `{namespace}` ({reason})\n"
        f"*Cause:* {_clean(d.get('root_cause'), 500)}\n"
        f"*Fix:* {_clean(d.get('suggested_fix'), 800)}\n"
        f"*Confidence:* {d.get('confidence')}"
    )
    try:
        r = requests.post(url, json={"text": text}, timeout=10)
        return r.status_code == 200
    except requests.RequestException as e:
        print("Slack post failed:", e)
        return False