from __future__ import annotations
import re
from multiprocessing import Process, Queue
from typing import Any, Dict, List
import traceback
import os

# configurable default timeout (seconds)
DEFAULT_TIMEOUT = float(os.getenv("AE_PY_EXEC_TIMEOUT", "8.0"))

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

def _extract_code_block(text: str) -> str:
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()

def _exec_worker(code: str, q: Queue):
    """Run untrusted code with a tiny builtin whitelist; no imports allowed."""
    import io, contextlib, types, re

    allowed_builtins = {
        "print": print, "range": range, "len": len, "int": int, "str": str,
        "list": list, "tuple": tuple, "dict": dict, "enumerate": enumerate,
        "sum": sum, "min": min, "max": max, "abs": abs,
    }
    forbidden = [
        r"__import__", r"\bimport\b", r"\bopen\s*\(", r"\bexec\s*\(",
        r"\beval\s*\(", r"\bos\.", r"\bsys\.", r"\bsubprocess\b", r"\bsocket\b",
        r"\brequests\b", r"\bshutil\b", r"\bpickle\b", r"\bctypes\b",
    ]
    for pat in forbidden:
        if re.search(pat, code):
            q.put({"ok": False, "error": f"Forbidden pattern: {pat}", "stdout": ""})
            return

    stdout = io.StringIO()
    try:
        sandbox_globals = {"__builtins__": types.MappingProxyType(allowed_builtins)}
        with contextlib.redirect_stdout(stdout):
            exec(compile(code, "<sandbox>", "exec"), sandbox_globals, {})
        q.put({"ok": True, "error": None, "stdout": stdout.getvalue()})
    except Exception:
        q.put({"ok": False, "error": "".join(traceback.format_exc()), "stdout": stdout.getvalue()})

def _run_code_with_timeout(code: str, timeout_s: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    q: Queue = Queue(maxsize=1)
    p = Process(target=_exec_worker, args=(code, q))
    p.start()
    p.join(timeout=timeout_s)
    if p.is_alive():
        p.terminate()
        p.join(0.2)
        return {"ok": False, "error": "Timeout", "stdout": ""}
    if q.empty():
        return {"ok": False, "error": "No result from sandbox", "stdout": ""}
    return q.get()

def evaluate_code_output(model_output: str, expected_sequence: List[int], timeout_s: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Extract code, execute, parse stdout ints, compare to expected."""
    code = _extract_code_block(model_output)
    res = _run_code_with_timeout(code, timeout_s=timeout_s)
    if not res.get("ok"):
        return {"ok": False, "reason": f"Execution error: {res.get('error')}", "got": [], "expected": expected_sequence, "stdout": res.get("stdout", "")}

    import re as _re
    got = [int(x) for x in _re.findall(r"-?\d+", res.get("stdout", ""))]
    return {
        "ok": got == expected_sequence,
        "reason": "" if got == expected_sequence else "Mismatch",
        "got": got,
        "expected": expected_sequence,
        "stdout": res.get("stdout", "")
    }
