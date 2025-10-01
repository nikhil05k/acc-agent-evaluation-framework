from typing import Any, Dict
import time

from crewai import Agent as CrewAgent, Task, Crew, LLM
from common.agents.base import AgentSpec, AgentIO, AgentResult
from frameworks.base import FrameworkAdapter
from configs.config import settings


class CrewAIAdapter(FrameworkAdapter):
    name = "crewai"

    def create_agent(self, spec: AgentSpec, **kwargs: Any) -> CrewAgent:
        """Turn our AgentSpec into a CrewAI Agent."""
        llm = LLM(
            model=spec.model or "gpt-4o-mini",
            temperature=spec.temperature,
            # api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        return CrewAgent(
            role=spec.name,
            goal=spec.system_prompt,
            backstory="A coding agent that writes Python snippets.",
            allow_delegation=False,
            verbose=False,
            llm=llm,
        )

    def run(self, agent: CrewAgent, io: AgentIO, **kwargs: Any) -> AgentResult:
        """Run the agent on the given task input."""
        start = time.perf_counter()

        # Build a CrewAI Task
        user_msg = next((m for m in io.messages if m["role"] == "user"), {})
        task = Task(
            description=user_msg.get("content", ""),
            agent=agent,
            expected_output="A valid Python code snippet that prints the first 10 numbers of the Fibonacci sequence.",
        )

        crew = Crew(agents=[agent], tasks=[task])
        raw_output = crew.kickoff()

        elapsed = time.perf_counter() - start

        # Normalize into AgentResult
        result = AgentResult(
            output_text=str(raw_output),
            usage={},  # CrewAI doesn't expose tokens directly (yet)
            timings={"framework_run_s": elapsed},
            tool_calls=[],
            raw=raw_output,
        )
        return result
