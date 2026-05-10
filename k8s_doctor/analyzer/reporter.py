from rich.console import Console
from rich.rule import Rule
from k8s_doctor.models import Report, Severity

console = Console()

_COLOR = {
    Severity.CRITICAL: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "blue",
}

_ICON = {
    Severity.CRITICAL: "❌",
    Severity.WARNING: "⚠️ ",
    Severity.INFO: "ℹ️ ",
}


def print_report(report: Report) -> None:
    console.print(Rule("[bold]k8s-doctor[/bold]"))
    console.print(f"[bold]Repo:[/bold] {report.repo_url}")
    console.print(
        f"[dim]Scanned {len(report.resources)} resources · "
        f"{len(report.issues)} issues found[/dim]\n"
    )

    if not report.issues:
        console.print("[green]✅  No issues found — looks good![/green]")
        return

    console.print(
        f"[red]❌ CRITICAL: {len(report.critical)}[/red]  "
        f"[yellow]⚠️  WARNING: {len(report.warnings)}[/yellow]  "
        f"[blue]ℹ️  INFO: {len(report.info)}[/blue]\n"
    )

    for severity in (Severity.CRITICAL, Severity.WARNING, Severity.INFO):
        for issue in report.issues:
            if issue.severity != severity:
                continue
            color = _COLOR[severity]
            icon = _ICON[severity]
            console.print(f"[{color}]{icon} {issue.title}[/{color}]")
            console.print(f"   [dim]{issue.file}[/dim]")
            console.print(f"   {issue.description}")
            if issue.fix:
                console.print(f"   [green]Fix:[/green] {issue.fix}")
            console.print()
