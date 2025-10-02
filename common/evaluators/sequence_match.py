import re
from typing import List, Dict, Any

def evaluate(output: str, expected_sequence: List[int]) -> Dict[str, Any]:
    got = [int(x) for x in re.findall(r"-?\d+", output)]
    return {
        "ok": got == expected_sequence,
        "got": got,
        "expected": expected_sequence,
        "reason": "" if got == expected_sequence else "Mismatch"
    }
