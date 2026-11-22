import json

from kubedoctor.diagnose import build_evidence

print(json.dumps(build_evidence("leaky"), indent=2, default=str))