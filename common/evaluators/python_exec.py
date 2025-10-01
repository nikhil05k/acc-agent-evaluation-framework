from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re

from common.agents.base import PythonExecTool

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

def _extract_code(text: str) -> Tuple[str, str]:
    """Return (language, code). If no fenced block, treat whole text as code."""
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return ("python", m.group(1).strip())
    return ("python", text.strip())

def _parse_ints_from_stdout(stdout: str) -> List[int]:
    """Extract integers in order from stdout (robust to spaces/newlines/commas)."""
    return [int(x) for x in re.findall(r"-?\d+", stdout)]

class PythonSnippetEvaluator:
    """Executes a Python snippet and compares its printed ints against an expected sequence."""
    name = "python_snippet_eval"

    def __init__(self, time_limit_s: float = 15) -> None:
        self.exec_tool = PythonExecTool(time_limit_s=time_limit_s)

    def evaluate(self, output_text: str, *, expected_sequence: List[int]) -> Dict[str, Any]:
        lang, code = _extract_code(output_text)
        if lang.lower() != "python":
            return {
                "ok": False,
                "reason": f"Non-Python code block detected: {lang}",
                "stdout": "",
                "got": [],
                "expected": expected_sequence,
            }

        # run safely
        try:
            res = self.exec_tool.call(code=code)
            stdout = (res or {}).get("stdout", "")
        except Exception as e:
            # one gentle retry with a longer timeout (helps first-run spawn costs on Windows/PyCharm)
            if "timed out" in str(e).lower():
                try:
                    self.exec_tool = PythonExecTool(time_limit_s=20.0)
                    res = self.exec_tool.call(code=code)
                    stdout = (res or {}).get("stdout", "")
                except Exception as e2:
                    return {
                        "ok": False,
                        "reason": f"Execution error after retry: {type(e2).__name__}: {e2}",
                        "stdout": "",
                        "got": [],
                        "expected": expected_sequence,
                    }
            else:
                return {
                    "ok": False,
                    "reason": f"Execution error: {type(e).__name__}: {e}",
                    "stdout": "",
                    "got": [],
                    "expected": expected_sequence,
                }

        got = _parse_ints_from_stdout(stdout)
        ok = got == expected_sequence
        return {
            "ok": ok,
            "reason": "" if ok else "Mismatch",
            "stdout": stdout,
            "got": got,
            "expected": expected_sequence,
        }
