import json

from kubedoctor.k8s_tools import list_unhealthy_pods
from kubedoctor.diagnose import diagnose

for item in list_unhealthy_pods():
    print("\n=====", item["pod"], "(", item["reason"], ") =====")
    print(json.dumps(diagnose(item["pod"]), indent=2))