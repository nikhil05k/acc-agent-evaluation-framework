from typing import Any, Dict, List

class SuccessRateMetric:
    name = "success_rate"

    def __init__(self, required_keywords: List[str] | None = None) -> None:
        self.required_keywords = required_keywords or ["print"]

    def compute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        output = result.get("output_text", "") or ""
        passed = all(keyword in output for keyword in self.required_keywords)
        return {self.name: 1.0 if passed else 0.0}
