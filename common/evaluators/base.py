from __future__ import annotations
from typing import Dict, Any, Protocol

class Evaluator(Protocol):
    """Evaluates a model output and returns a structured result."""
    name: str
    def evaluate(self, output_text: str, **kwargs: Any) -> Dict[str, Any]: ...
