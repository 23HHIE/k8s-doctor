import json
import os
from typing import Optional

import anthropic

from k8s_doctor.models import Issue, K8sResource, Report, Severity

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def enrich_report(report: Report) -> None:
    """Add AI-detected issues to report.issues (mutates in place)."""
    if not report.resources:
        return

    # Summarise all resources as compact YAML-like text to keep tokens low
    resource_summary = "\n\n".join(
        f"# {r.file} — {r.kind}/{r.name}\n{json.dumps(r.raw, indent=2)}"
        for r in report.resources
    )

    prompt = f"""You are a Kubernetes security and reliability expert.
Review these K8s manifests and identify issues NOT already in this list:
{[i.title for i in report.issues]}

Return a JSON array of objects with keys:
  severity: "CRITICAL" | "WARNING" | "INFO"
  title: short title
  description: one sentence
  file: which file
  fix: one-line fix suggestion

Manifests:
{resource_summary}

Return ONLY valid JSON array, no markdown, no explanation."""

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        raw = response.content[0].text.strip()
        items = json.loads(raw)
        for item in items:
            report.issues.append(Issue(
                severity=Severity[item["severity"]],
                title=item["title"],
                description=item["description"],
                file=item.get("file", "unknown"),
                fix=item.get("fix"),
            ))
    except (json.JSONDecodeError, KeyError):
        # AI response was malformed — silently skip, rule-based checks still run
        pass
