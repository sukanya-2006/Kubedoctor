import os

import requests
from dotenv import load_dotenv

load_dotenv(override=True)
url = os.getenv("SLACK_WEBHOOK_URL")

if not url:
    print("SLACK_WEBHOOK_URL is missing from .env")
else:
    r = requests.post(url, json={"text": "KubeDoctor test message"}, timeout=10)
    print(r.status_code, r.text)