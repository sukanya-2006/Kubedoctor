import os
import time

from kubedoctor.diagnose import diagnose
from kubedoctor.k8s_tools import list_unhealthy_pods
from kubedoctor.notify import send_slack

NAMESPACE = os.getenv("WATCH_NAMESPACE", "default")
INTERVAL = int(os.getenv("WATCH_INTERVAL", "60"))
IGNORE = {"kubedoctor"}  # don't diagnose ourselves


def main():
    seen = set()
    print(f"KubeDoctor watching namespace '{NAMESPACE}' every {INTERVAL}s", flush=True)
    while True:
        try:
            current = {
                i["pod"]: i["reason"]
                for i in list_unhealthy_pods(NAMESPACE)
                if not any(i["pod"].startswith(p) for p in IGNORE)
            }
            for pod, reason in current.items():
                if pod in seen:
                    continue
                try:
                    d = diagnose(pod, NAMESPACE)
                    print(pod, "->", d.get("root_cause"), flush=True)
                    send_slack(pod, NAMESPACE, reason, d)
                except Exception as e:
                    print("could not diagnose", pod, e, flush=True)
                seen.add(pod)
                time.sleep(5)  # stay under the free-tier rate limit
            seen &= set(current)  # forget recovered pods so they can alert again
        except Exception as e:
            print("watch loop error:", e, flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()