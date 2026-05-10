from pathlib import Path
from k8s_doctor.analyzer.parser import parse_manifests

FIXTURES = Path(__file__).parent / "fixtures"

def _load(filename: str) -> dict[str, str]:
    return {filename: (FIXTURES / filename).read_text()}

def test_parse_deployment():
    resources = parse_manifests(_load("bad_deployment.yaml"))
    assert len(resources) == 1
    assert resources[0].kind == "Deployment"
    assert resources[0].name == "bad-app"
    assert resources[0].namespace == "default"
    assert resources[0].file == "bad_deployment.yaml"

def test_skip_non_k8s_yaml():
    files = {"config.yaml": "host: localhost\nport: 5432\n"}
    resources = parse_manifests(files)
    assert resources == []

def test_parse_multiple_docs_in_one_file():
    content = (FIXTURES / "bad_deployment.yaml").read_text()
    content += "\n---\n"
    content += (FIXTURES / "good_deployment.yaml").read_text()
    resources = parse_manifests({"multi.yaml": content})
    assert len(resources) == 2
