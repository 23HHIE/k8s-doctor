from k8s_doctor.models import Issue, K8sResource, Severity


def run_checks(resources: list[K8sResource]) -> list[Issue]:
    """Run all checks and return issues."""
    issues: list[Issue] = []
    for resource in resources:
        issues.extend(_check_resource(resource))
    issues.extend(_check_cross_file(resources))
    return issues


def _check_resource(resource: K8sResource) -> list[Issue]:
    if resource.kind in ("Deployment", "StatefulSet", "DaemonSet"):
        return _check_workload(resource)
    return []


def _check_workload(resource: K8sResource) -> list[Issue]:
    issues: list[Issue] = []
    spec = resource.raw.get("spec", {})
    containers = (
        spec
        .get("template", {})
        .get("spec", {})
        .get("containers", [])
    )

    for container in containers:
        name = container.get("name", "unknown")

        # Image tag
        image = container.get("image", "")
        if not image or image.endswith(":latest") or ":" not in image:
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Image uses :latest tag",
                description=f"Container '{name}' uses a mutable image tag.",
                file=resource.file,
                fix='Pin to a specific version, e.g. "myapp:1.2.3"',
            ))

        # Resource limits
        res = container.get("resources", {})
        if not res.get("limits"):
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Missing resource limits",
                description=f"Container '{name}' has no resource limits — can starve other pods.",
                file=resource.file,
                fix="Add resources.limits.cpu and resources.limits.memory",
            ))
        if not res.get("requests"):
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Missing resource requests",
                description=f"Container '{name}' has no resource requests — scheduler cannot place it optimally.",
                file=resource.file,
                fix="Add resources.requests.cpu and resources.requests.memory",
            ))

        # Probes
        if not container.get("livenessProbe"):
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Missing livenessProbe",
                description=f"Container '{name}' has no livenessProbe — stuck pods won't restart.",
                file=resource.file,
                fix="Add a livenessProbe with httpGet, exec, or tcpSocket",
            ))
        if not container.get("readinessProbe"):
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Missing readinessProbe",
                description=f"Container '{name}' has no readinessProbe — unready pods may receive traffic.",
                file=resource.file,
                fix="Add a readinessProbe to control traffic routing",
            ))

        # Security context
        sc = container.get("securityContext", {})
        if sc.get("privileged"):
            issues.append(Issue(
                severity=Severity.CRITICAL,
                title="Privileged container",
                description=f"Container '{name}' runs with full host privileges.",
                file=resource.file,
                fix="Set securityContext.privileged: false",
            ))
        if not sc.get("runAsNonRoot"):
            issues.append(Issue(
                severity=Severity.WARNING,
                title="Container may run as root",
                description=f"Container '{name}' does not enforce non-root execution.",
                file=resource.file,
                fix="Set securityContext.runAsNonRoot: true",
            ))

        # readOnlyRootFilesystem
        if not sc.get("readOnlyRootFilesystem"):
            issues.append(Issue(
                severity=Severity.INFO,
                title="Container filesystem is writable",
                description=f"Container '{name}' does not use a read-only root filesystem.",
                file=resource.file,
                fix="Set securityContext.readOnlyRootFilesystem: true",
            ))

    # Rolling update strategy
    strategy = spec.get("strategy", {}).get("type", "")
    if strategy != "RollingUpdate":
        issues.append(Issue(
            severity=Severity.INFO,
            title="Not using RollingUpdate strategy",
            description=f"Deployment '{resource.name}' does not use RollingUpdate.",
            file=resource.file,
            fix="Set spec.strategy.type: RollingUpdate",
        ))

    # Default namespace
    if resource.namespace == "default":
        issues.append(Issue(
            severity=Severity.INFO,
            title="Resource in default namespace",
            description=f"{resource.kind} '{resource.name}' is in the default namespace.",
            file=resource.file,
            fix="Use a dedicated namespace (e.g. production, staging)",
        ))

    return issues


def _check_cross_file(resources: list[K8sResource]) -> list[Issue]:
    issues: list[Issue] = []

    deployments = {r.name: r for r in resources if r.kind == "Deployment"}
    services = {r.name: r for r in resources if r.kind == "Service"}

    # Service selector must match at least one Deployment's pod labels
    for svc_name, svc in services.items():
        selector = svc.raw.get("spec", {}).get("selector", {})
        if not selector:
            continue
        matched = any(
            all(
                dep.raw.get("spec", {})
                .get("template", {})
                .get("metadata", {})
                .get("labels", {})
                .get(k) == v
                for k, v in selector.items()
            )
            for dep in deployments.values()
        )
        if not matched:
            issues.append(Issue(
                severity=Severity.CRITICAL,
                title="Service selector matches no Deployment",
                description=f"Service '{svc_name}' selector {selector} matches no Deployment pod labels.",
                file=svc.file,
                fix="Ensure Deployment spec.template.metadata.labels match Service spec.selector",
            ))

    # HPA must target an existing Deployment
    for resource in resources:
        if resource.kind != "HorizontalPodAutoscaler":
            continue
        target = resource.raw.get("spec", {}).get("scaleTargetRef", {}).get("name")
        if target and target not in deployments:
            issues.append(Issue(
                severity=Severity.CRITICAL,
                title="HPA targets non-existent Deployment",
                description=f"HPA '{resource.name}' targets Deployment '{target}' which was not found.",
                file=resource.file,
                fix=f"Create a Deployment named '{target}' or correct the HPA scaleTargetRef",
            ))

    return issues
