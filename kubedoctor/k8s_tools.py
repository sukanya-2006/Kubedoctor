from kubernetes import client, config


def _load():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


_load()
v1 = client.CoreV1Api()


def list_unhealthy_pods(namespace="default"):
    out = []
    for p in v1.list_namespaced_pod(namespace).items:
        reason = None
        for cs in (p.status.container_statuses or []):
            waiting = cs.state.waiting
            terminated = cs.state.terminated or cs.last_state.terminated
            if waiting and waiting.reason not in (None, "ContainerCreating"):
                reason = waiting.reason
            elif terminated and terminated.reason != "Completed":
                reason = terminated.reason
        if reason is None and p.status.phase == "Pending" and not p.status.container_statuses:
            reason = "Pending"
        if reason:
            out.append({"pod": p.metadata.name, "reason": reason})
    return out


def get_pod_events(pod, namespace="default"):
    ev = v1.list_namespaced_event(
        namespace, field_selector=f"involvedObject.name={pod}"
    )
    return [f"{e.type} {e.reason}: {e.message}" for e in ev.items]


def get_pod_logs(pod, namespace="default", tail=50):
    try:
        return v1.read_namespaced_pod_log(
            pod, namespace, tail_lines=tail, previous=True
        )
    except client.ApiException:
        try:
            return v1.read_namespaced_pod_log(pod, namespace, tail_lines=tail)
        except client.ApiException as e:
            return f"(no logs available: {e.reason})"


def describe_pod(pod, namespace="default"):
    p = v1.read_namespaced_pod(pod, namespace)
    return {
        "phase": p.status.phase,
        "containers": [
            {
                "name": c.name,
                "image": c.image,
                "resources": c.resources.to_dict() if c.resources else {},
            }
            for c in p.spec.containers
        ],
        "statuses": [cs.to_dict() for cs in (p.status.container_statuses or [])],
    }