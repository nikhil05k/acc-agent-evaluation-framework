from __future__ import annotations
from crewai import Agent, Task, Crew, LLM
from crewai_tools import CodeInterpreterTool, SerperDevTool


class CrewaiRunner:
    name = "crewai"

    def run_fibonacci(self, system_prompt: str, user_prompt: str, model: str, temperature: float
                      ) -> str:
        # Note: CrewAI will use the model configured in your env (e.g., OPENAI_API_KEY).
        llm = LLM(
            model=model,
            temperature=temperature,
            # api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        agent = Agent(
            role="Python Coder",
            goal=system_prompt,
            backstory="Writes small, correct Python snippets.",
            allow_delegation=False,
            verbose=False,
            llm=llm,
        )
        task = Task(
            description=user_prompt,
            agent=agent,
            expected_output="Return only a Python fenced code block (```python ... ```)."
        )
        crew = Crew(agents=[agent], tasks=[task])
        return str(crew.kickoff()).strip()

    def run_fibonacci_exec(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        llm = LLM(
            model=model,
            temperature=temperature,
            # api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        agent = Agent(
            role="Python Programmer",
            goal=system_prompt,
            backstory="An expert Python programmer who can write efficient code to solve complex problems.",
            allow_delegation=False,
            verbose=True,
            tools=[CodeInterpreterTool()],  # ✅ execution tool
            llm=llm,
        )
        task = Task(
            description=user_prompt,
            agent=agent,
            expected_output="The Fibonacci sequence up to the 10th number.",
        )
        crew = Crew(agents=[agent], tasks=[task])
        return str(crew.kickoff()).strip()

    def run_websearch(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        # Configure search tool (requires SERPER_API_KEY in env)
        search_tool = SerperDevTool()

        llm = LLM(
            model=model,
            temperature=temperature,
            base_url="https://openrouter.ai/api/v1"
        )

        agent = Agent(
            role="Research Assistant",
            goal=system_prompt,
            backstory="An assistant who researches online and provides clear summaries.",
            allow_delegation=False,
            verbose=True,
            tools=[search_tool],
            llm=llm,
        )

        task = Task(
            description=user_prompt,
            agent=agent,
            expected_output="A concise 3–5 sentence summary including the words 'Starship' and 'SpaceX'."
        )

        crew = Crew(agents=[agent], tasks=[task])
        return str(crew.kickoff()).strip()