from typing import Any, Dict

class CostMetric:
    name = "cost"

    def compute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        usage = result.get("usage", {})
        return {self.name: usage.get("cost", None)}
