from __future__ import annotations
import os

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"

import argparse, importlib, time
from common.utils.prompt_builder import load_case, get_prompts, get_llm_config
from metrics import latency as m_latency
from metrics import success_keywords as m_keywords
from metrics import functional_correctness as m_correct
from metrics import tool_usage as m_tool
from metrics import cost as m_cost
from dotenv import load_dotenv

# load .env if present
load_dotenv()


def run_case_framework(case_name: str, framework: str) -> dict:
    case = load_case(case_name)
    system_prompt, user_prompt = get_prompts(case)
    temperature, model_name = get_llm_config(case)

    # Load framework runner class: e.g., frameworks.crewai_runner.CrewAIRunner
    module = importlib.import_module(f"frameworks.{framework}_runner")
    class_name = f"{framework.capitalize()}Runner"
    runner = getattr(module, class_name)()

    # Case-specific method pattern: run_<case>
    method_name = f"run_{case_name}"
    if not hasattr(runner, method_name):
        raise NotImplementedError(f"{class_name} does not implement {method_name}()")

    run_func = getattr(runner, method_name)

    # Measure latency
    t0 = time.perf_counter()
    output_text = run_func(system_prompt, user_prompt, model_name, temperature)
    t1 = time.perf_counter()
    elapsed = t1 - t0

    # Build metrics from case.yaml
    expectations = case.get("expectations", {}) or {}
    metric_list = case.get("metrics", []) or []

    scores = {}
    for m in metric_list:
        if m == "latency":
            scores.update(m_latency.as_metric(elapsed))
        elif m == "success_keywords":
            scores.update(m_keywords.score(output_text, expectations.get("contains", [])))
        elif m == "functional_correctness":
            expected_seq = expectations.get("expected_sequence") or []
            scores.update(m_correct.score(output_text, expected_seq))
        elif m == "tool_usage":
            scores.update(m_tool.score(output_text))
        elif m == "sequence_correctness":
            from metrics import sequence_correctness as m_seq
            expected_seq = expectations.get("expected_sequence") or []
            scores.update(m_seq.score(output_text, expected_seq))

        # elif m == "cost":
        #     scores.update(m_cost.score(None))

    return {
        "case": case_name,
        "framework": framework,
        "output": output_text,
        "metrics": scores,
    }


def main():
    ap = argparse.ArgumentParser(description="Agent Eval Runner")
    ap.add_argument("--frameworks", "-f", type=str, default="crewai",
                    help="Comma-separated frameworks (e.g., crewai,adk)")
    ap.add_argument("--cases", "-c", type=str, default="fibonacci",
                    help="Comma-separated case names (e.g., fibonacci,sorting)")
    args = ap.parse_args()

    frameworks = [x.strip() for x in args.frameworks.split(",") if x.strip()]
    cases = [x.strip() for x in args.cases.split(",") if x.strip()]

    all_results = []
    for case_name in cases:
        for fw in frameworks:
            res = run_case_framework(case_name, fw)
            all_results.append(res)
            # simple console report
            print(f"\n=== CASE: {case_name} | FRAMEWORK: {fw} ===")
            print(res["output"])
            print("Metrics:", res["metrics"])


if __name__ == "__main__":
    main()
