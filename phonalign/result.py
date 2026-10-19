from dataclasses import dataclass, field


@dataclass
class Result:
    units: list
    posterior: float = None
    confidences: list = None
    rows: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)
