from pathlib import Path
from k8s_doctor.analyzer.parser import parse_manifests
from k8s_doctor.analyzer.checker import run_checks
from k8s_doctor.models import Severity

FIXTURES = Path(__file__).parent / "fixtures"

def _resources(filename: str):
    content = (FIXTURES / filename).read_text()
    return parse_manifests({filename: content})

def test_bad_deployment_has_issues():
    resources = _resources("bad_deployment.yaml")
    issues = run_checks(resources)
    titles = [i.title for i in issues]
    assert any("latest" in t.lower() for t in titles)
    assert any("privileged" in t.lower() for t in titles)
    assert any("resource" in t.lower() for t in titles)
    assert any("liveness" in t.lower() for t in titles)

def test_bad_deployment_has_critical_for_privileged():
    resources = _resources("bad_deployment.yaml")
    issues = run_checks(resources)
    critical_titles = [i.title for i in issues if i.severity == Severity.CRITICAL]
    assert any("privileged" in t.lower() for t in critical_titles)

def test_good_deployment_has_no_security_issues():
    resources = _resources("good_deployment.yaml")
    issues = run_checks(resources)
    critical = [i for i in issues if i.severity == Severity.CRITICAL]
    assert critical == []

def test_mismatched_service_selector():
    resources = _resources("mismatched_service.yaml")
    issues = run_checks(resources)
    assert any("selector" in i.title.lower() for i in issues)
    assert any(i.severity == Severity.CRITICAL for i in issues)

def test_orphan_hpa():
    resources = _resources("orphan_hpa.yaml")
    issues = run_checks(resources)
    assert any("HPA" in i.title for i in issues)
    assert any(i.severity == Severity.CRITICAL for i in issues)
