from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Protocol, runtime_checkable, Optional
import json
import re
import time

from multiprocessing import Process, Queue
import traceback

def _exec_worker(code: str, q: Queue):
    """Run untrusted code in a restricted namespace and return stdout or error via Queue."""
    import io, contextlib, types, re

    # very restricted builtins
    allowed_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "str": str,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "enumerate": enumerate,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
    }

    # block dangerous names
    forbidden_patterns = [
        r"__import__",
        r"\bopen\s*\(",
        r"\bexec\s*\(",
        r"\beval\s*\(",
        r"\bos\.",
        r"\bsys\.",
        r"\bsubprocess\b",
        r"\bshutil\b",
        r"\bsocket\b",
        r"\brequests\b",
        r"\bpickle\b",
        r"\bctypes\b",
        r"\bpathlib\b",
        r"\bimport\b",        # disallow imports entirely for this evaluator
    ]
    for pat in forbidden_patterns:
        if re.search(pat, code):
            q.put({"ok": False, "error": f"Use of forbidden pattern in code: {pat}", "stdout": ""})
            return

    stdout = io.StringIO()
    try:
        sandbox_globals = {"__builtins__": types.MappingProxyType(allowed_builtins)}
        with contextlib.redirect_stdout(stdout):
            exec(compile(code, "<python_exec_tool>", "exec"), sandbox_globals, {})
        q.put({"ok": True, "error": None, "stdout": stdout.getvalue()})
    except Exception:
        q.put({"ok": False, "error": "".join(traceback.format_exc()), "stdout": stdout.getvalue()})


# -----------------------------
# Tooling (framework-agnostic)
# -----------------------------

@runtime_checkable
class ToolSpec(Protocol):
    """Framework-agnostic Tool interface.

    A Tool is a pure Python callable with:
      - name: stable identifier
      - description: short human-readable info for the model/prompt
      - schema: optional JSON schema (dict) for arguments validation/UX

    Tools should be deterministic and side-effect aware (idempotent where possible).
    """
    name: str
    description: str
    schema: Optional[Dict[str, Any]]

    def call(self, **kwargs) -> Any: ...


class ToolError(RuntimeError):
    pass


def safe_tool_call(tool: ToolSpec, **kwargs) -> Dict[str, Any]:
    """Run a tool and capture timing + errors in a structured way."""
    started = time.perf_counter()
    try:
        output = tool.call(**kwargs)
        ok = True
        err = None
    except Exception as e:
        output = None
        ok = False
        err = f"{type(e).__name__}: {e}"
    elapsed = time.perf_counter() - started
    return {"ok": ok, "error": err, "latency_s": elapsed, "output": output, "tool": tool.name, "args": kwargs}


# -----------------------------
# Memory (short & long-term)
# -----------------------------

@runtime_checkable
class MemorySpec(Protocol):
    """Abstract memory protocol.

    Implementations can be in-memory, file-backed, vector DB, etc.
    """

    def put(self, key: str, value: Any) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def delete(self, key: str) -> None: ...
    def keys(self) -> Iterable[str]: ...
    def to_dict(self) -> Dict[str, Any]: ...


class InMemoryMemory(MemorySpec):
    """Simple ephemeral key-value store. Good enough for initial cases & tests."""
    def __init__(self, initial: Optional[Mapping[str, Any]] = None) -> None:
        self._store: Dict[str, Any] = dict(initial or {})

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def keys(self) -> Iterable[str]:
        return self._store.keys()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._store)


# -----------------------------
# Agent specification & runtime
# -----------------------------

@dataclass
class AgentSpec:
    """Framework-agnostic description of an agent."""
    name: str
    system_prompt: str
    model: Optional[str] = None
    temperature: float = 0.2
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    memory: Optional[MemorySpec] = None
    tools: List[ToolSpec] = field(default_factory=list)

    def add_tool(self, tool: ToolSpec) -> None:
        self.tools.append(tool)

    def set_memory(self, memory: MemorySpec) -> None:
        self.memory = memory


@dataclass
class AgentIO:
    """Standardized IO envelope passed to frameworks (messages in/out)."""
    # Minimal chat schema that any provider can map to.
    messages: List[Dict[str, Any]]

    def token_estimate(self) -> int:
        # deliberately simple heuristic; concrete providers should override with real counts
        return sum(len(m.get("content", "")) // 4 + 1 for m in self.messages)

    @classmethod
    def from_text(cls, system: str, user: str) -> "AgentIO":
        return cls(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])


@dataclass
class AgentResult:
    """Unified result format returned by any framework adapter."""
    output_text: str
    usage: Dict[str, Any] = field(default_factory=dict)     # tokens, cost, etc.
    timings: Dict[str, float] = field(default_factory=dict) # latency, etc.
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw: Any = None                                          # provider/framework raw result


# -----------------------------
# Utility helpers (prompting)
# -----------------------------

def render_prompt(template: str, **vars: Any) -> str:
    """A tiny Jinja-free renderer for simple {{var}} replacements to avoid early deps.
    (You can swap to Jinja2 later; keeping this minimal for first pass.)
    """
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return str(vars.get(key, ""))
    return re.sub(r"\{\{\s*(.*?)\s*\}\}", replace, template)


def ensure_code_fence(s: str, lang: str = "python") -> str:
    """Wrap output in a fenced code block if not already fenced."""
    if "```" in s:
        return s
    return f"```{lang}\n{s.strip()}\n```"


# -----------------------------
# Minimal built-in tool (optional but handy early on)
# -----------------------------

# --- replace the existing PythonExecTool class in common/agents/base.py ---
class PythonExecTool:
    """Execute a short Python snippet in a restricted child process with a timeout.
    Cross-platform (works on Windows/macOS/Linux). No imports, no file/network access.
    """

    name = "python_exec"
    description = "Execute a short Python snippet in a restricted namespace and return stdout."
    schema = {
        "type": "object",
        "properties": {"code": {"type": "string", "description": "Python code to execute"}},
        "required": ["code"],
        "additionalProperties": False,
    }

    def __init__(self, time_limit_s: float = 2.0) -> None:
        self.time_limit_s = float(time_limit_s)

    def call(self, *, code: str) -> Dict[str, Any]:
        q: Queue = Queue(maxsize=1)
        p = Process(target=_exec_worker, args=(code, q))
        p.start()
        p.join(timeout=self.time_limit_s)

        if p.is_alive():
            p.terminate()
            p.join(0.2)
            raise ToolError("Code execution timed out.")

        if q.empty():
            # Child crashed before posting a result
            raise ToolError("Execution failed with no result from sandboxed process.")

        res = q.get()
        if not res.get("ok"):
            raise ToolError(res.get("error") or "Unknown execution error.")
        return {"stdout": res.get("stdout", "")}
