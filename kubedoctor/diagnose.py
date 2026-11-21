import json
import os

from dotenv import load_dotenv
from groq import Groq

from . import k8s_tools as k

load_dotenv(override=True)

# Groq's model names change over time. Check console.groq.com for the current list,
# and set GROQ_MODEL in .env if this one is not available.
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
client = Groq()  # reads GROQ_API_KEY from .env

HINTS = {
    "ImagePullBackOff": "The container image could not be pulled (bad name/tag, or registry access).",
    "ErrImagePull": "The container image could not be pulled (bad name/tag, or registry access).",
    "CrashLoopBackOff": "The container keeps crashing on startup; check the logs.",
    "OOMKilled": "The container used more memory than its limit; check the memory limit.",
    "Pending": "The pod cannot be scheduled; check resource requests and node capacity.",
}

SYSTEM = """You are a Kubernetes SRE helping a beginner.
You are given evidence about one failing pod.
Rules:
- Read the "logs" first. If the logs contain an error message, that is usually the root cause.
- Only make claims about things that appear in the evidence. Never assume a setting is missing
  unless the evidence shows it is missing.
- Quote exact log or event lines in "evidence".
Reply with ONLY a JSON object, no other text, with these keys:
  "root_cause": one or two plain-English sentences,
  "category": one of ImagePull, CrashLoop, OOMKilled, Config, Scheduling, Other,
  "evidence": a list of the exact log or event lines that support your answer,
  "suggested_fix": concrete steps to fix it,
  "confidence": "low", "medium" or "high"."""

def _reason_for(pod, namespace):
    for item in k.list_unhealthy_pods(namespace):
        if item["pod"] == pod:
            return item["reason"]
    return None


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def diagnose(pod, namespace="default"):
    reason = _reason_for(pod, namespace)
    evidence = {
        "pod": pod,
                "logs": (k.get_pod_logs(pod, namespace) or "")[-2000:],
        "status_reason": reason,
        "hint": HINTS.get(reason, ""),
        "describe": k.describe_pod(pod, namespace),
        "events": k.get_pod_events(pod, namespace)[-15:],
    }
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(evidence, default=str)},
        ],
    )
    return _parse_json(resp.choices[0].message.content)