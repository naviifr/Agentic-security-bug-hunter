from dataclasses import dataclass, field
from typing import Any

@dataclass
class Result:
    file: str
    findings: list
    plg_data: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

@dataclass
class Finding:
    file: str
    function: str | None
    line: int | None
    cwe: str | None
    confidence: str | None
    source: list[str] = field(default_factory=list)