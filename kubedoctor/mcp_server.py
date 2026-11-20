from mcp.server.fastmcp import FastMCP

from kubedoctor import k8s_tools as k
from kubedoctor.diagnose import diagnose

mcp = FastMCP("kubedoctor")


@mcp.tool()
def list_unhealthy_pods(namespace: str = "default") -> list:
    """List pods that are crashing, pending, or failing to start."""
    return k.list_unhealthy_pods(namespace)


@mcp.tool()
def get_pod_events(pod: str, namespace: str = "default") -> list:
    """Get recent Kubernetes events for a pod."""
    return k.get_pod_events(pod, namespace)


@mcp.tool()
def get_pod_logs(pod: str, namespace: str = "default") -> str:
    """Get recent logs for a pod, including from its previous crashed container."""
    return k.get_pod_logs(pod, namespace)


@mcp.tool()
def diagnose_pod(pod: str, namespace: str = "default") -> dict:
    """Diagnose why a pod is failing and suggest a fix."""
    return diagnose(pod, namespace)


if __name__ == "__main__":
    mcp.run()  # stdio transport