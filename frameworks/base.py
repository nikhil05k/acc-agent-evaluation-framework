from __future__ import annotations
from typing import Any, Dict, Protocol
from common.agents.base import AgentSpec, AgentResult, AgentIO


class FrameworkAdapter(Protocol):
    """Every framework adapter must implement this interface."""

    name: str

    def create_agent(self, spec: AgentSpec, **kwargs: Any) -> Any:
        """Create a framework-native agent from a framework-agnostic AgentSpec.

        Args:
            spec: AgentSpec containing system_prompt, model, memory, tools, etc.
            kwargs: Extra config to pass through (e.g., tracing, logging).

        Returns:
            A framework-native agent object.
        """
        ...

    def run(self, agent: Any, io: AgentIO, **kwargs: Any) -> AgentResult:
        """Execute a task on the given agent using the provided I/O.

        Args:
            agent: Framework-native agent created via create_agent().
            io: AgentIO containing messages (system, user, etc.)
            kwargs: Extra options (trace_id, temperature override, etc.)

        Returns:
            AgentResult containing normalized output, usage, timings, raw response.
        """
        ...
