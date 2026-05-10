from k8s_doctor.models import Issue, K8sResource, Report, Severity


def test_issue_creation():
    issue = Issue(
        severity=Severity.CRITICAL,
        title="Privileged container",
        description="Container runs as privileged",
        file="deployment.yaml",
    )
    assert issue.severity == Severity.CRITICAL
    assert issue.line is None  # optional field defaults to None


def test_report_severity_grouping():
    issues = [
        Issue(Severity.CRITICAL, "A", "desc", "f.yaml"),
        Issue(Severity.WARNING, "B", "desc", "f.yaml"),
        Issue(Severity.WARNING, "C", "desc", "f.yaml"),
        Issue(Severity.INFO, "D", "desc", "f.yaml"),
    ]
    report = Report(repo_url="https://github.com/x/y", issues=issues)
    assert len(report.critical) == 1
    assert len(report.warnings) == 2
    assert len(report.info) == 1
