import os
import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import google_search
from google.genai import types  # needed to construct messages


class AdkRunner:
    name = "adk"

    async def _collect_response_async(self, runner: Runner, user_prompt: str, session_id: str) -> str:
        """
        Run the agent and collect final response using async API.
        """
        message = types.Content(role="user", parts=[types.Part(text=user_prompt)])

        final_result = None
        stream_accum = []
        code_execution_output = None

        async for event in runner.run_async(user_id="user", session_id=session_id, new_message=message):
            # Debug: Print event details
            print(f"DEBUG EVENT: id={event.id}, author={event.author}, final={event.is_final_response()}")

            # Check for code execution results in ANY event (not just final)
            if event.content and event.content.parts:
                for i, part in enumerate(event.content.parts):
                    print(
                        f"  Part {i}: executable_code={hasattr(part, 'executable_code') and part.executable_code is not None}, "
                        f"code_execution_result={hasattr(part, 'code_execution_result') and part.code_execution_result is not None}, "
                        f"text={hasattr(part, 'text') and part.text is not None}")

                    # Check for code execution result
                    if hasattr(part, "code_execution_result") and part.code_execution_result:
                        code_execution_output = part.code_execution_result.output
                        print(f"  CODE EXECUTION OUTPUT: {code_execution_output}")
                    # Collect streaming text
                    elif hasattr(part, "text") and part.text and getattr(event, "partial", False):
                        stream_accum.append(part.text)
                        print(f"  STREAMING TEXT: {part.text[:50]}...")

            if event.is_final_response():
                print(f"FINAL EVENT - code_execution_output: {code_execution_output}")
                # If we got code execution output, prefer that
                if code_execution_output:
                    final_result = code_execution_output.strip()
                elif event.content and event.content.parts:
                    # Otherwise, try to get text response
                    part0 = event.content.parts[0]
                    if hasattr(part0, "text") and part0.text:
                        final_result = ("".join(stream_accum) + part0.text).strip()
                    else:
                        responses = event.get_function_responses()
                        if responses:
                            final_result = str(responses[0].response)
                break

        print(f"FINAL RESULT: {final_result}")
        return final_result or ""

    def _collect_response(self, runner: Runner, user_prompt: str, session_id: str) -> str:
        """Synchronous wrapper for _collect_response_async."""
        return asyncio.run(self._collect_response_async(runner, user_prompt, session_id))

    def run_fibonacci(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        app_name = "fibonacci"
        session_id = "session1"

        agent = LlmAgent(
            name="fibonacci_agent",
            model=model,
            instruction=system_prompt,
        )

        # Create session service
        session_service = InMemorySessionService()

        # Create session using asyncio
        asyncio.run(session_service.create_session(
            app_name=app_name,
            user_id="user",
            session_id=session_id
        ))

        # Create runner with the session service
        runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

        return self._collect_response(runner, user_prompt, session_id=session_id)

    def run_fibonacci_exec(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        app_name = "fibonacci_exec"
        session_id = "session1"

        agent = LlmAgent(
            name="fibonacci_exec_agent",
            model=model,
            instruction=system_prompt,
            code_executor=BuiltInCodeExecutor(),  # ✅ enable code execution

        )

        # Create session service
        session_service = InMemorySessionService()

        # Create session using asyncio
        asyncio.run(session_service.create_session(
            app_name=app_name,
            user_id="user",
            session_id=session_id
        ))

        # Create runner with the session service
        runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

        return self._collect_response(runner, user_prompt, session_id=session_id)

    def run_websearch(self, system_prompt: str, user_prompt: str, model: str, temperature: float) -> str:
        app_name = "websearch"
        session_id = "session1"

        agent = LlmAgent(
            name="websearch_agent",
            model=model,
            instruction=system_prompt,
            tools=[google_search],   # ✅ enable Google Search tool
        )

        # Create session service
        session_service = InMemorySessionService()

        # Create session
        asyncio.run(session_service.create_session(
            app_name=app_name,
            user_id="user",
            session_id=session_id
        ))

        # Create runner
        runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

        # Collect response
        return self._collect_response(runner, user_prompt, session_id=session_id)
