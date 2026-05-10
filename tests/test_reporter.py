from k8s_doctor.analyzer.reporter import print_report
from k8s_doctor.models import Issue, Report, Severity

def _make_report(issues: list[Issue]) -> Report:
    return Report(repo_url="https://github.com/test/repo", issues=issues)

def test_print_report_no_issues(capsys):
    report = _make_report([])
    # Should not raise
    print_report(report)

def test_print_report_shows_severity_counts(capsys):
    issues = [
        Issue(Severity.CRITICAL, "Priv container", "desc", "f.yaml"),
        Issue(Severity.WARNING, "Latest tag", "desc", "f.yaml"),
    ]
    report = _make_report(issues)
    print_report(report)
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.out
    assert "WARNING" in captured.out
