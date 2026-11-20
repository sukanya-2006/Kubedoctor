from kubedoctor.k8s_tools import list_unhealthy_pods, get_pod_events, get_pod_logs

pods = list_unhealthy_pods()
print(pods)

for p in pods:
    print("\n=====", p["pod"], "=====")
    print(get_pod_events(p["pod"]))
    print(get_pod_logs(p["pod"]))