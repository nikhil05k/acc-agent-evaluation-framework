from typing import Dict
from common.agents.base import AgentSpec, InMemoryMemory, PythonExecTool

# Central registry of available agent specs
_AGENT_SPECS: Dict[str, AgentSpec] = {}


def register_agent(name: str, spec: AgentSpec) -> None:
    """Register a new AgentSpec under a name."""
    if name in _AGENT_SPECS:
        raise ValueError(f"Agent spec already registered: {name}")
    _AGENT_SPECS[name] = spec


def get_agent_spec(name: str) -> AgentSpec:
    """Retrieve an AgentSpec by name."""
    print(_AGENT_SPECS)
    try:
        return _AGENT_SPECS[name]
    except KeyError:
        raise ValueError(f"Unknown agent spec: {name}. Registered: {list(_AGENT_SPECS)}")


def list_agent_specs() -> Dict[str, AgentSpec]:
    """Return all registered agent specs."""
    return dict(_AGENT_SPECS)


# -------------------------
# Predefined starter agents
# -------------------------

# A simple coder agent (useful for Fibonacci case)
register_agent(
    "SimpleCoder",
    AgentSpec(
        name="SimpleCoder",
        system_prompt="You are a helpful Python coding assistant. "
                      "Write clean, minimal, and correct code snippets.",
        model="gpt-4o-mini",  # default model, can be overridden in case.yaml
        memory=InMemoryMemory(),
        tools=[PythonExecTool()],
    ),
)

# You could add more later (Analyst, Researcher, Summarizer, etc.)
