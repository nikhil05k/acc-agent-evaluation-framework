from __future__ import annotations
from typing import Any, Dict, List

from common.evaluators.base import Evaluator

class FunctionalCorrectnessMetric:
    """Returns 1.0 if evaluator.ok else 0.0, plus attaches evaluator details."""
    name = "functional_correctness"

    def __init__(self, evaluator: Evaluator, *, expected_sequence: List[int]) -> None:
        self.evaluator = evaluator
        self.expected_sequence = expected_sequence

    def compute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        output = result.get("output_text", "") or ""
        eval_res = self.evaluator.evaluate(output_text=output, expected_sequence=self.expected_sequence)
        score = 1.0 if eval_res.get("ok") else 0.0
        # also expose details for debugging
        return {
            self.name: score,
            f"{self.name}_details": {
                "ok": eval_res.get("ok"),
                "reason": eval_res.get("reason"),
                "got": eval_res.get("got"),
                "expected": eval_res.get("expected"),
            },
        }
