# KubeDoctor

An AI assistant that diagnoses broken Kubernetes pods and explains the fix in plain English.

## Status
Work in progress.

## Plan
- Chaos scenarios that break pods on purpose
- Python tools that read pod events and logs
- LLM diagnosis with suggested fixes
- MCP server so AI assistants can call the tools
- Docker, Kubernetes manifests, and Helm chart
- Benchmark: how many failures it diagnoses correctly