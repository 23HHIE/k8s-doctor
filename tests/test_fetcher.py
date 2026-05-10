from unittest.mock import patch, MagicMock
from k8s_doctor.analyzer.fetcher import fetch_yaml_files, _parse_repo
import base64


def test_parse_repo_https():
    owner, repo = _parse_repo("https://github.com/alexuser/my-app")
    assert owner == "alexuser"
    assert repo == "my-app"


def test_parse_repo_with_git_suffix():
    owner, repo = _parse_repo("https://github.com/alexuser/my-app.git")
    assert owner == "alexuser"
    assert repo == "my-app"


def test_parse_repo_invalid():
    import pytest
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        _parse_repo("https://gitlab.com/user/repo")


def test_fetch_yaml_files_returns_content():
    tree_response = MagicMock()
    tree_response.json.return_value = {
        "tree": [
            {"type": "blob", "path": "k8s/deployment.yaml"},
            {"type": "blob", "path": "k8s/service.yml"},
            {"type": "blob", "path": "README.md"},  # should be skipped
        ]
    }
    tree_response.raise_for_status = MagicMock()

    content_response = MagicMock()
    content_response.json.return_value = {
        "content": base64.b64encode(b"apiVersion: apps/v1\nkind: Deployment").decode()
    }
    content_response.raise_for_status = MagicMock()

    with patch("k8s_doctor.analyzer.fetcher.requests.get") as mock_get:
        mock_get.side_effect = [tree_response, content_response, content_response]
        result = fetch_yaml_files("https://github.com/alexuser/my-app")

    assert "k8s/deployment.yaml" in result
    assert "k8s/service.yml" in result
    assert "README.md" not in result
    assert "kind: Deployment" in result["k8s/deployment.yaml"]
