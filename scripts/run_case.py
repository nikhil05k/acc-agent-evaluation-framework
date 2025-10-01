import argparse
import os
import time
import yaml
from pathlib import Path


from common.evaluators.python_exec import PythonSnippetEvaluator
from common.metrics.functional_correctness import FunctionalCorrectnessMetric
from common.agents.registry import get_agent_spec
from common.agents.base import AgentIO, AgentResult
from common.metrics.latency import LatencyMetric
from common.metrics.success_rate import SuccessRateMetric
from common.metrics.cost import CostMetric
from frameworks.base import FrameworkAdapter


from frameworks.crewai.adapter import CrewAIAdapter


def load_yaml(path: str | Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_prompt(path: str | Path, **vars) -> str:
    text = Path(path).read_text()
    # simple replacement using render_prompt from base.py if needed
    from common.agents.base import render_prompt
    return render_prompt(text, **vars)


def run_case(case_path: str, framework: FrameworkAdapter) -> dict:
    # ---------------------------
    # 1. Load case config
    # ---------------------------
    case = load_yaml(case_path)
    agent_cfg = case["agents"][0]

    # ---------------------------
    # 2. Resolve AgentSpec
    # ---------------------------
    agent_spec = get_agent_spec(agent_cfg["spec"])
    if "model" in agent_cfg:
        agent_spec.model = agent_cfg["model"]

    # ---------------------------
    # 3. Load prompts
    # ---------------------------
    system_prompt = load_prompt(case["prompts"]["system"], language="Python")
    user_prompt = load_prompt(case["prompts"]["user"])

    io = AgentIO.from_text(system_prompt, user_prompt)

    # ---------------------------
    # 4. Create agent via adapter
    # ---------------------------
    agent = framework.create_agent(agent_spec)

    # ---------------------------
    # 5. Run agent on task
    # ---------------------------
    t0 = time.perf_counter()
    result: AgentResult = framework.run(agent, io)
    t1 = time.perf_counter()
    result.timings["total_s"] = t1 - t0

    # ---------------------------
    # 6. Compute metrics
    # ---------------------------
    expectations = case.get("expectations", {}) or {}
    expected_seq = expectations.get("expected_sequence", None)

    metrics = [
        LatencyMetric(),
        SuccessRateMetric(required_keywords=expectations.get("contains", [])),
        CostMetric(),
    ]
    if expected_seq:
        evaluator = PythonSnippetEvaluator(time_limit_s=2.0)
        metrics.append(FunctionalCorrectnessMetric(evaluator, expected_sequence=expected_seq))

    scores = {}
    for metric in metrics:
        scores.update(metric.compute(result.__dict__))

    # ---------------------------
    # 7. Print summary
    # ---------------------------
    print("\n=== Case Result ===")
    print("Case:", case["name"])
    print("Framework:", framework.name)
    print("Output:\n", result.output_text)
    print("Metrics:", scores)

    return {"case": case["name"], "framework": framework.name, "output": result.output_text, "metrics": scores}


def main():
    parser = argparse.ArgumentParser(description="Run a case against a framework")
    parser.add_argument("--case", required=True, help="Path to case.yaml")
    parser.add_argument("--framework", required=False, default="crewai", help="Framework name")
    args = parser.parse_args()

    # TEMP: only CrewAI later — for now raise if not implemented
    if args.framework == "crewai":
        framework = CrewAIAdapter()
    else:
        raise ValueError(f"Unsupported framework: {args.framework}")

    run_case(args.case, framework)


if __name__ == "__main__":
    print("----------------------")
    print(os.getenv("OPENAI_API_KEY"))
    print(os.getenv("OPENROUTER_API_KEY"))
    print("----------------------")
    main()
