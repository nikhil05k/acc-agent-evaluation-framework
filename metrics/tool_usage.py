def score(raw_output: str) -> dict:
    # crude check — improve later if CrewAI gives structured traces
    used = "CodeInterpreterTool" in str(raw_output) or "executed code" in str(raw_output).lower()
    return {"tool_usage": 1.0 if used else 0.0}
