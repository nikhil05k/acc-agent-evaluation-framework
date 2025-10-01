from __future__ import annotations
from typing import Any, Dict, Protocol


class Metric(Protocol):
    """Protocol for all metrics. Every metric must have a name and compute()."""
    name: str

    def compute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Compute metric given a unified AgentResult (as dict).

        Returns a dict {metric_name: value}.
        """
        ...
