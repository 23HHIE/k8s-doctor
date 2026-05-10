from typing import Any
import yaml
from k8s_doctor.models import K8sResource

K8S_KINDS = {
    "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob",
    "Service", "Ingress",
    "HorizontalPodAutoscaler",
    "ConfigMap", "Secret",
    "PersistentVolumeClaim",
    "Namespace", "ServiceAccount",
    "Role", "RoleBinding", "ClusterRole", "ClusterRoleBinding",
}


def parse_manifests(files: dict[str, str]) -> list[K8sResource]:
    """Parse YAML files and return all recognised K8s resources."""
    resources: list[K8sResource] = []
    for filepath, content in files.items():
        for doc in yaml.safe_load_all(content):
            if not isinstance(doc, dict):
                continue
            if doc.get("kind") not in K8S_KINDS:
                continue
            resources.append(
                K8sResource(
                    kind=doc["kind"],
                    name=doc.get("metadata", {}).get("name", "unknown"),
                    namespace=doc.get("metadata", {}).get("namespace", "default"),
                    file=filepath,
                    raw=doc,
                )
            )
    return resources
