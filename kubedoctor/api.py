from fastapi import FastAPI, HTTPException

from kubedoctor import k8s_tools as k
from kubedoctor.diagnose import diagnose

app = FastAPI(title="KubeDoctor")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/incidents")
def incidents(namespace: str = "default"):
    return k.list_unhealthy_pods(namespace)


@app.post("/diagnose/{pod}")
def diagnose_pod(pod: str, namespace: str = "default"):
    try:
        return diagnose(pod, namespace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))