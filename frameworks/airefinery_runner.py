import os
import asyncio
import uuid

from air import AsyncAIRefinery
from dotenv import load_dotenv
from air import DistillerClient
import yaml

load_dotenv()  # ensures GEMINI / AI_REFINERY keys are loaded

class AirefineryRunner:
    name = "airefinery"

    def __init__(self, model: str | None = None):
        self.api_key = os.getenv("AI_REFINERY_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing AI_REFINERY_API_KEY in environment")
        self.client = AsyncAIRefinery(api_key=self.api_key)
        self.distiller_client = DistillerClient(api_key=self.api_key)

        # choose default model if not passed
        self.model = model or os.getenv("AI_REFINERY_MODEL", "gpt-4o-mini")

    async def _call(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        """
        Make a call to AI Refinery using the Async client.
        """
        # Combine system + user into one request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        resp = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2
        )
        return resp.choices[0].message["content"].strip()

    async def _query_distiller(self, project: str, prompt: str, uuid: str = "test_user", version: str = "1") -> str:
        """
        Run a query against a Distiller project and return concatenated responses.
        """
        # distiller_client = DistillerClient(api_key=self.api_key)
        result_text = []
        async with self.distiller_client(
                project=project,
                uuid="test_user",
        ) as dc:
            responses = await dc.query(
                query=prompt
            )  # send the query to be processed
            result_text = []
            async for response in responses:
                result_text.append(response.get('content'))

        return "\n".join(result_text).strip()

    def run_fibonacci(self, system_prompt: str, user_prompt: str, model: str = None, temperature: float = 0.2) -> str:
        """
        Case 1: Code generation (like CrewAI + ADK).
        """
        return asyncio.run(self._call(system_prompt, user_prompt, model=model, temperature=temperature))

    def run_fibonacci_exec(self, system_prompt: str, user_prompt: str, model: str = None, temperature: float = 0.2) -> str:
        """
        Case 2: Code execution.
        AI Refinery does not ship a generic interpreter, so:
        - Ask model to return code
        - Execute locally in sandbox (reuse your existing python_code_eval evaluator)
        """
        code_output = asyncio.run(self._call(system_prompt, user_prompt, model=model, temperature=temperature))

        # Now reuse your evaluator to run code safely
        from common.evaluators import python_code_eval
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        result = python_code_eval.evaluate_code_output(code_output, expected)
        return str(result.get("stdout") or result.get("got"))

    def run_websearch(self, system_prompt: str, user_prompt: str, model: str = None, temperature: float = 0.2) -> str:
        project = "gardening_project"  # must exist with SearchAgent config
        # self.distiller_client.create_project(
        #     config_path="config.yaml",
        #     project=project
        # )
        return asyncio.run(self._query_distiller(project, user_prompt, uuid='9fda635a-eee5-47a2-9488-c1b9af702b46'))