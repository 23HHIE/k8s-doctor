import os
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from k8s_doctor.analyzer.ai_analyzer import enrich_report
from k8s_doctor.analyzer.checker import run_checks
from k8s_doctor.analyzer.fetcher import fetch_yaml_files
from k8s_doctor.analyzer.parser import parse_manifests
from k8s_doctor.analyzer.reporter import print_report
from k8s_doctor.models import Report

load_dotenv()
app = typer.Typer(help="Audit Kubernetes manifests in a GitHub repository.")
console = Console()


@app.command()
def main(
    repo_url: str = typer.Argument(..., help="GitHub repo URL to audit"),
    github_token: Optional[str] = typer.Option(
        None, envvar="GITHUB_TOKEN", help="GitHub token (required for private repos)"
    ),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip Claude AI enrichment"),
) -> None:
    """Audit a GitHub repo's Kubernetes manifests."""
    console.print(f"[dim]Fetching manifests from {repo_url} ...[/dim]")
    try:
        files = fetch_yaml_files(repo_url, github_token)
    except Exception as e:
        console.print(f"[red]Error fetching repo:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[dim]Found {len(files)} YAML files[/dim]")

    resources = parse_manifests(files)
    console.print(f"[dim]Parsed {len(resources)} K8s resources[/dim]\n")

    issues = run_checks(resources)
    report = Report(repo_url=repo_url, resources=resources, issues=issues)

    if not no_ai and os.getenv("ANTHROPIC_API_KEY"):
        console.print("[dim]Running AI analysis ...[/dim]")
        enrich_report(report)

    print_report(report)

    # Exit code: 1 if any CRITICAL issues
    if report.critical:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
