from dataclasses import dataclass, field
from typing import Any

@dataclass
class Result:
    file: str
    plg_data: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)