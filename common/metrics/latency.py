import time
from typing import Any, Dict

class LatencyMetric:
    name = "latency"

    def compute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # We expect result["timings"]["total_s"] to be set by the runner
        latency = result.get("timings", {}).get("total_s", None)
        return {self.name: latency}
