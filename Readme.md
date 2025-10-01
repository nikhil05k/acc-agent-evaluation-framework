
# `README.md`

# Agent Evaluation Framework

A lightweight, extensible framework for **evaluating agentic frameworks** (e.g. CrewAI, LangGraph, AutoGen, AdalFlow) across consistent tasks, prompts, and metrics.

The goal: **apples-to-apples comparison** of how different agent frameworks handle the same scenarios.

---

## 🚀 Features

- **Framework-agnostic interface**  
  One adapter contract (`FrameworkAdapter`) so any agent framework can be plugged in.

- **Case-based evaluation**  
  Define tasks in YAML (`cases/`) with agents, prompts, and metrics.  
  Example: *generate a Python snippet for Fibonacci.*

- **Reusable prompts**  
  Centralized system/task prompts in `common/prompts/`.

- **Unified agent specs**  
  Framework-independent `AgentSpec` with memory, tools, and defaults (`common/agents/`).

- **Metrics-first design**  
  Out-of-the-box metrics for:
  - Latency
  - Cost
  - Keyword-based success rate
  - Functional correctness (executes generated Python snippets safely in a sandbox)

- **Cross-platform code execution**  
  Generated Python snippets are sandboxed in a child process with timeout, safe on Linux/macOS/Windows.

---

## 📂 Repository Structure


```

agent-evals/  
├─ common/  
│ ├─ agents/ # AgentSpec, registry, tool/memory interfaces  
│ ├─ prompts/ # System & task prompts (Jinja2 templates)  
│ ├─ metrics/ # Metric implementations  
│ └─ evaluators/ # Evaluators (e.g. Python snippet correctness)  
├─ frameworks/  
│ ├─ base.py # FrameworkAdapter interface  
│ └─ crewai/ # CrewAI adapter (first supported framework)  
├─ cases/  
│ └─ fibonacci/ # First case (Python Fibonacci code snippet)  
├─ scripts/  
│ └─ run_case.py # Runner CLI  
└─ results/ # (to be populated with outputs, scores, reports)

```

---

## ⚡ Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt

```

Dependencies include:

-   `crewai`
    
-   `langchain-openai`
    
-   `python-dotenv`
    
-   `pyyaml`
    

### 2. Configure API keys

Add an `.env` file in the project root:

```
OPENROUTER_API_KEY=sk-...

```

### 3. Run the Fibonacci case

```bash
python scripts/run_case.py --case cases/fibonacci/case.yaml --framework crewai

```

### Example output

```
=== Case Result ===
Case: fibonacci
Framework: crewai
Output:
 def fibonacci(n):
     a, b = 0, 1
     for _ in range(n):
         print(a)
         a, b = b, a + b

 fibonacci(10)

Metrics: {
  'latency': 5.50,
  'success_rate': 1.0,
  'cost': None,
  'functional_correctness': 1.0,
  'functional_correctness_details': {
    'ok': True,
    'got': [0,1,1,2,3,5,8,13,21,34],
    'expected': [0,1,1,2,3,5,8,13,21,34]
  }
}

```

----------

## 🧩 Adding New Frameworks

1.  Create a subdir under `frameworks/` (e.g. `frameworks/langgraph/adapter.py`).
    
2.  Implement the `FrameworkAdapter` interface:
    
    -   `create_agent(spec: AgentSpec)`
        
    -   `run(agent, io: AgentIO) -> AgentResult`
        
3.  Register it in the runner.
    

----------

## 📈 Adding New Cases

1.  Create a folder under `cases/` (e.g. `cases/sorting/`).
    
2.  Add `case.yaml`:
    
    ```yaml
    name: sorting
    description: Generate Python code to sort a list.
    agents:
      - id: coder
        spec: SimpleCoder
        model: gpt-4o-mini
    prompts:
      system: common/prompts/system/default_system.j2
      user: common/prompts/task/sorting_user.j2
    metrics:
      - functional_correctness
    expectations:
      expected_sequence: [1, 2, 3, 4, 5]
    
    ```
    
3.  Add prompt file under `common/prompts/task/`.
    

----------

## 📊 Next Steps

-   Add more frameworks (LangGraph, AutoGen, AdalFlow).
    
-   Build richer evaluators (RAG precision/recall, reasoning trace checks).
    
-   Store run results under `results/` and auto-generate leaderboards.
    
-   Add CI to ensure reproducibility of cases and metrics.
    


👉 This `README.md` is written so that **a new contributor can clone, set their key, and run the Fibonacci case right away**.  


```