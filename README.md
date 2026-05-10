# k8s-doctor

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

> Audit Kubernetes manifests in a GitHub repository. Paste a URL, get a health report.

```bash
pip install k8s-doctor
k8s-doctor https://github.com/your-org/your-app
```

## What it checks

**Security**
- Privileged containers
- Containers running as root
- Images using `:latest` tag

**Reliability**
- Missing `livenessProbe` / `readinessProbe`
- Missing resource requests/limits
- Single replica with no HPA

**Cross-file consistency**
- Service selector matches no Deployment
- HPA targets a non-existent Deployment

**AI-powered analysis** (requires `ANTHROPIC_API_KEY`)
- Deeper context-aware issues beyond static rules

## Setup

```bash
# Optional — for private repos and AI analysis
export GITHUB_TOKEN=ghp_...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
# Public repo
k8s-doctor https://github.com/org/repo

# Private repo
k8s-doctor https://github.com/org/repo --github-token $GITHUB_TOKEN

# Skip AI analysis
k8s-doctor https://github.com/org/repo --no-ai
```

## Example output

```
──────────────────── k8s-doctor ────────────────────
Repo: https://github.com/example/my-app
Scanned 8 resources · 6 issues found

❌ CRITICAL: 2  ⚠️  WARNING: 3  ℹ️  INFO: 1

❌ Privileged container
   k8s/deployment.yaml
   Container 'app' runs with full host privileges.
   Fix: Set securityContext.privileged: false

⚠️  Missing livenessProbe
   k8s/deployment.yaml
   Container 'app' has no livenessProbe — stuck pods won't restart.
   Fix: Add a livenessProbe with httpGet, exec, or tcpSocket
```

## License

MIT
