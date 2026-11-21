import json
import subprocess
import textwrap
import time

from kubedoctor.diagnose import diagnose
from kubedoctor.k8s_tools import list_unhealthy_pods

NS = "bench"

TEMPLATE = """apiVersion: v1
kind: Pod
metadata:
  name: {name}
spec:
  containers:
    - name: app
{body}
"""

# expected = acceptable categories; keywords = at least one must appear in the
# root cause or fix. A scenario passes only if BOTH checks pass.
SCENARIOS = [
    {
        "name": "bad-tag",
        "body": "image: nginx:does-not-exist",
        "expected": ["ImagePull"],
        "keywords": ["not found", "tag", "exist"],
    },
    {
        "name": "bad-registry",
        "body": "image: registry.invalid/team/app:1.0",
        "expected": ["ImagePull"],
        "keywords": ["registry", "host", "dns", "resolve"],
    },
    {
        "name": "invalid-image-name",
        "body": 'image: "nginx::bad"',
        "expected": ["ImagePull"],
        "keywords": ["invalid", "image name", "format", "tag"],
    },
    {
        "name": "missing-env-crash",
        "body": """image: busybox
command: ["sh", "-c", "echo 'FATAL: DB_URL is not set' >&2; exit 1"]""",
        "expected": ["Config", "CrashLoop"],
        "keywords": ["db_url"],
    },
    {
        "name": "db-unreachable",
        "body": """image: busybox
command: ["sh", "-c", "echo 'ERROR: could not connect to postgres at db:5432 (connection refused)' >&2; exit 1"]""",
        "expected": ["CrashLoop", "Other", "Config"],
        "keywords": ["connect", "postgres", "database", "db:5432"],
    },
    {
        "name": "oom",
        "body": """image: polinux/stress
command: ["stress", "--vm", "1", "--vm-bytes", "200M"]
resources:
  limits:
    memory: "50Mi\"""",
        "expected": ["OOMKilled"],
        "keywords": ["memory", "oom", "limit"],
    },
    {
        "name": "bad-command",
        "body": """image: busybox
command: ["/bin/doesnotexist"]""",
        "expected": ["Config", "CrashLoop", "Other"],
        "keywords": ["executable", "not found", "command", "exist"],
    },
    {
        "name": "pending-cpu",
        "allow_pending": True,
        "body": """image: busybox
command: ["sleep", "3600"]
resources:
  requests:
    cpu: "1000\"""",
        "expected": ["Scheduling"],
        "keywords": ["cpu", "insufficient", "schedul"],
    },
    {
        "name": "missing-configmap",
        "body": """image: busybox
command: ["sleep", "3600"]
env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: LOG_LEVEL""",
        "expected": ["Config"],
        "keywords": ["configmap"],
    },
    {
        "name": "missing-secret",
        "body": """image: busybox
command: ["sleep", "3600"]
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: password""",
        "expected": ["Config"],
        "keywords": ["secret"],
    },
]


def kubectl(*args, stdin=None):
    return subprocess.run(
        ["kubectl", *args], input=stdin, text=True, capture_output=True
    )


def wait_unhealthy(name, allow_pending=False, timeout=180):
    end = time.time() + timeout
    while time.time() < end:
        for item in list_unhealthy_pods(NS):
            if item["pod"] == name and (allow_pending or item["reason"] != "Pending"):
                return item["reason"]
        time.sleep(5)
    return None


def main():
    kubectl("create", "namespace", NS)
    results = []

    import sys
    only = sys.argv[1:]
    scenarios = [s for s in SCENARIOS if not only or s["name"] in only]

    for s in scenarios:
        name = s["name"]
        print(f"\n--- {name} ---")
        manifest = TEMPLATE.format(
            name=name, body=textwrap.indent(s["body"], "      ")
        )
        r = kubectl("apply", "-n", NS, "-f", "-", stdin=manifest)
        if r.returncode != 0:
            print("could not create pod:", r.stderr.strip())
            results.append({"scenario": name, "passed": False, "note": "apply failed"})
            continue

        reason = wait_unhealthy(name, s.get("allow_pending", False))
        if reason is None:
            print("pod never showed a failure state (not detected)")
            results.append({"scenario": name, "passed": False, "note": "not detected"})
            kubectl("delete", "pod", name, "-n", NS, "--wait=false")
            continue

        time.sleep(15)  # let events and logs build up
        try:
            d = diagnose(name, NS)
        except Exception as e:
            print("diagnosis error:", e)
            results.append({"scenario": name, "passed": False, "note": f"error: {e}"})
            kubectl("delete", "pod", name, "-n", NS, "--wait=false")
            continue

        text = (str(d.get("root_cause")) + " " + str(d.get("suggested_fix"))).lower()
        cat_ok = d.get("category") in s["expected"]
        kw_ok = any(k in text for k in s["keywords"])
        passed = cat_ok and kw_ok

        print("status:", reason)
        print("category:", d.get("category"), "| category ok:", cat_ok, "| keyword ok:", kw_ok)
        print("root cause:", d.get("root_cause"))
        print("RESULT:", "PASS" if passed else "FAIL")

        results.append({
            "scenario": name,
            "status": reason,
            "category": d.get("category"),
            "root_cause": d.get("root_cause"),
            "passed": passed,
        })

        kubectl("delete", "pod", name, "-n", NS, "--wait=false")
        time.sleep(5)  # stay under the free-tier rate limit

    kubectl("delete", "namespace", NS, "--wait=false")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print("\n==============================")
    print(f"ACCURACY: {passed}/{total} ({100 * passed // total}%)")
    for r in results:
        print(("PASS  " if r["passed"] else "FAIL  ") + r["scenario"])

    with open("benchmark/results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("saved benchmark/results.json")


if __name__ == "__main__":
    main()