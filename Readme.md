# 🧪 Agentic Framework Evaluation

This project provides a **unified evaluation harness** for comparing different **agentic frameworks** (CrewAI, ADK, AI Refinery SDK, etc.) across a common set of tasks.  
It is designed to highlight **strengths, limitations, and opportunities** across frameworks in terms of setup, LLM compatibility, tool usage, orchestration, and enterprise readiness.

----------

## 📌 Features

-   **Common Case Definitions**:  
    Prompts and expected outputs defined in YAML (`common/cases/`)
    
-   **Pluggable Framework Runners**:  
    Each framework (CrewAI, ADK, AI Refinery) has its own runner class implementing a shared interface
    
-   **Unified Evaluation**:  
    Run the same case across multiple frameworks and compare outputs + metrics
    
-   **Metrics Engine**:  
    Latency, correctness, success rate, tool usage, etc.  
    Extensible for new evaluation dimensions
    

----------

## 📂 Directory Structure

```
agent-evaluation-framework/
│
├── common/
│   ├── cases/             # YAML definitions of evaluation cases
│   ├── evaluators/        # Code correctness, functional checks
│   ├── metrics/           # Metrics calculators (latency, cost, correctness)
│   └── utils/             # Shared utilities (prompt builder, runner helpers)
│
├── frameworks/
│   ├── crewai_runner.py   # CrewAI integration
│   ├── adk_runner.py      # ADK (Gemini) integration
│   └── airefinery_runner.py # AI Refinery SDK integration
│
├── runner.py              # Common entrypoint to run evaluations
└── README.md              # This file

```

----------

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone <git url>
cd acc-agent-evaluation-framework

```

### 2. Install Dependencies

Create a virtual environment and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

```

### 3. Configure API Keys

Create a `.env` file in the project root with keys for the frameworks you want to evaluate based on `.env.example`

### 4. Run Evaluations

Run a specific case on a framework:

```bash
python runner.py --frameworks crewai --cases fibonacci

```

Run multiple frameworks on multiple cases:

```bash
python runner.py --frameworks crewai adk airefinery --cases fibonacci fibonacci_exec websearch

```

----------

## 🧪 Example Cases

-   **fibonacci** – Generate Python code to print the first 10 Fibonacci numbers.
    
-   **fibonacci_exec** – Execute Fibonacci code and validate numeric output.
    
-   **websearch** – Use framework’s search capabilities to answer factual queries.
    

Each case is defined in YAML with system/user prompts and expectations.

----------

## 📊 Metrics

Current metrics include:

-   **Latency** (time to first/full response)
    
-   **Success rate** (did it produce an answer?)
    
-   **Functional correctness** (does code run correctly?)
    
-   **Tool usage** (did the agent actually invoke a tool?)
    
-   **Keyword checks** (for factual answers)
    

More can be added easily in `common/metrics/`.

----------

## ➕ Adding New Frameworks

To add a new framework:

1.  Create a new runner in `frameworks/<framework>_runner.py`
    
2.  Implement methods for supported cases (e.g. `run_fibonacci`, `run_fibonacci_exec`, `run_websearch`)
    
3.  Ensure it conforms to the same interface as existing runners
    
4.  Register the framework in `runner.py`
    

----------

## 📈 Reporting

The framework can generate structured results (stdout, JSON, or markdown) to support comparative reports.  
See `Report.md` for a running evaluation summary.

----------

## 🙌 Contributing

This is an evolving framework. Contributions are welcome for:

-   New test cases (multi-agent workflows, RAG, planning, memory)
    
-   New frameworks (LangChain, AutoGen, etc.)
    
-   New metrics (cost, governance checks, observability)
   