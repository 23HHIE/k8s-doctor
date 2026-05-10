import base64
import re
from typing import Optional

import requests


def _parse_repo(repo_url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub HTTPS URL."""
    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    return match.group(1), match.group(2)


def fetch_yaml_files(
    repo_url: str, github_token: Optional[str] = None
) -> dict[str, str]:
    """Return {file_path: content} for all YAML files in the repo."""
    owner, repo = _parse_repo(repo_url)
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()

    yaml_files: dict[str, str] = {}
    for item in resp.json().get("tree", []):
        if item["type"] == "blob" and item["path"].endswith((".yaml", ".yml")):
            content_resp = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{item['path']}",
                headers=headers,
                timeout=30,
            )
            content_resp.raise_for_status()
            raw = base64.b64decode(content_resp.json()["content"]).decode("utf-8")
            yaml_files[item["path"]] = raw

    return yaml_files
