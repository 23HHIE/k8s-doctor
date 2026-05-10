from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Issue:
    severity: Severity
    title: str
    description: str
    file: str
    line: Optional[int] = None
    fix: Optional[str] = None


@dataclass
class K8sResource:
    kind: str
    name: str
    namespace: str
    file: str
    raw: dict


@dataclass
class Report:
    repo_url: str
    resources: list[K8sResource] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def critical(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.CRITICAL]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def info(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.INFO]
