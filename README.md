# Ask-the-Numbers: A Trustworthy Mini AI Business Intelligence Assistant

> *"Ask in plain English. Get answers you can audit."*

[![Python Tests](https://img.shields.io/badge/pytest-29%20passed-brightgreen.svg)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-blue.svg)](https://fastapi.tiangolo.com)
[![Zero-Key Ready](https://img.shields.io/badge/Zero--Key%20Mode-Supported-emerald.svg)](#zero-key-execution)
[![AWS Ready](https://img.shields.io/badge/AWS%20Lambda-Mangum%20Ready-orange.svg)](docs/AWS_DEPLOYMENT.md)

---

## 1. Executive Pitch

Most natural-language database assistants follow a risky design: *"LLM writes SQL → execute → show text."* When the LLM generates subtle arithmetic hallucinations, inverted date ranges, or ungrounded figures, business decisions suffer.

**Ask-the-Numbers** is engineered around an unshakeable reliability thesis:
> **The LLM never does math. It only decides what to ask. Every single number originates from a verified SQLite query, is cross-checked in parallel by an independent Pandas verification engine, and is displayed with a transparent Proof Panel.**

Built as a hiring assessment project for **RSG (Hyderabad) — Graduate Engineer Trainee (Python with Generative AI Engineer)**.

---

## 2. Key Highlights & USPs

1. **Three-Lane Question Router:**
   - **Lane A (Deterministic):** Pre-compiled, certified SQL templates for core executive metrics. 100% correct, zero LLM variance.
   - **Lane B (Guarded Text-to-SQL):** AST-inspected open queries via `sqlglot` on a read-only database.
   - **Lane C (Polite Refusal):** Destructive attacks (`DROP`, `DELETE`) and future forecasting questions are refused with clear context and 3 alternative recommendations.
2. **Dual-Engine Verification (USP-3):**
   - Every metric is independently computed by two distinct engines: SQLite and a Pandas pipeline loading the CSV directly. If both calculators do not agree within 0.01 tolerance, the answer is blocked.
3. **Data Quality & Quarantine (USP-4):**
   - 3 planted test cases in the 51-row dataset are transparently quarantined: `TXN0033` (returned), `TXN0034` (zero quantity), and `TXN0051` (missing unit price). They are never silently invented or imputed.
4. **Driver Analysis Agent (USP-5):**
   - 4-step autonomous reasoning (Plan → Query → Decompose → Narrate) for period-over-period questions (e.g. March vs April variance, "Why did May spike?", "Why did June drop?").
5. **Vectorless RAG (USP-6):**
   - Hierarchical data dictionary (`knowledge/glossary.json`) resolves business synonyms without embeddings, latency, or drift.
6. **Zero-Key Execution (USP-7):**
   - Fully operational out-of-the-box with **zero API keys** via `RuleBasedProvider`. Automatically upgrades to **Gemini 2.5 Flash** when `GEMINI_API_KEY` is supplied.

---

## 3. Dataset Golden Truth (Jan–Jun 2026)

All figures verified with 100% mathematical precision across 48 clean completed rows:

| Metric | Verified Golden Value |
|---|---|
| **Total Net Revenue** | **₹14,39,200** (₹14,58,200 if returns opted in) |
| **Top Product** | **Monitor — ₹4,73,000** (32.9% company revenue concentration) |
| **Top Region** | **South — ₹4,11,200** (North: 3,84,450; East: 3,46,700; West: 2,96,850) |
| **Category Breakdown** | Accessories: ₹5,33,100 · Electronics: ₹4,73,000 · Furniture: ₹4,33,100 |
| **Channel Breakdown** | Online: ₹7,46,750 · Retail: ₹6,92,450 |
| **Monthly Trend** | Jan: 2,10,250 · Feb: 2,34,600 · Mar: 2,23,900 · Apr: 2,40,700 · **May: 3,18,500 (Peak)** · Jun: 2,11,250 |
| **March to April Delta** | **+₹16,800 (+7.50%)** (Drivers: Wireless Mouse +22,100, USB-C Hub +14,400) |
| **Returns Quarantined** | **₹19,000** (1 order: TXN0033, Monitor) |
| **Average Order Value** | **₹29,983.33** |
| **Discount Impact** | **₹4,500** (0.31% of gross revenue) |

---

## 4. Quick Start (Run in 60 Seconds)

### Prerequisites
- Python 3.10+ installed
- Bash or PowerShell

### Linux / Mac
```bash
# 1. Clone repository
git clone <repo-url>
cd ask-the-numbers

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch application (Starts on http://localhost:8000)
python3 -m app
# or
make run
```

### Windows (PowerShell)
```powershell
python -m pip install -r requirements.txt
python -m app
```

Open your browser to: **`http://localhost:8000`**

---

## 5. Environment Variables (`.env`)

Configure in `.env` (optional — works completely without keys):

```env
# Optional: Set to enable Gemini Flash for open-ended Lane B questions
GEMINI_API_KEY="your-gemini-api-key"
LLM_MODEL="gemini-2.5-flash"

# Server configuration
PORT=8000
HOST="0.0.0.0"
```

---

## 6. Project Architecture & Directory Structure

```
ask-the-numbers/
├── app/
│   ├── main.py                 # FastAPI application & static server
│   ├── config.py               # Paths, model selection, currency config
│   ├── api/
│   │   ├── routes.py           # REST endpoints (/api/ask, /api/health, etc.)
│   │   └── schemas.py          # Pydantic request/response models
│   ├── core/
│   │   ├── metrics.py          # Single source of truth for formulas & INR formatting
│   │   ├── lane_a.py           # Certified deterministic SQL registry
│   │   ├── guard.py            # sqlglot AST SQL inspection & allowlist
│   │   ├── verifier.py         # Dual-Engine Pandas cross-checker
│   │   ├── agent_drivers.py    # 4-step period-over-period variance agent
│   │   ├── narrator.py         # Number-audited natural language narrator
│   │   ├── orchestrator.py     # End-to-end 7-step pipeline coordinator
│   │   └── vectorless_rag.py   # Hierarchical glossary retriever
│   ├── llm/
│   │   ├── gemini.py           # Modern google-genai client
│   │   └── rule_based.py       # Zero-key deterministic router
│   ├── data/
│   │   ├── etl.py              # CSV loader, strict dd-mm-yyyy parsing, quarantine
│   │   └── quality.py          # Data quality reporting models
│   ├── knowledge/
│   │   └── glossary.json       # Business glossary & entity synonyms
│   └── static/
│       ├── index.html          # Executive single-page dashboard
│       ├── app.js              # Chart.js visualization & interactive proof panels
│       └── style.css           # Modern dark executive theme
├── tests/
│   ├── test_etl.py             # Date parsing and quarantine assertions
│   ├── test_metrics_golden.py  # Golden metrics re-computed with Pandas & SQL
│   ├── test_router.py          # Router intent & security checks
│   ├── test_guard_security.py  # Red-team SQL injection suite
│   ├── test_drivers.py         # Variance decomposition tests
│   └── test_api.py             # Integration tests for all REST endpoints
├── docs/
│   ├── ARCHITECTURE.md         # Full Mermaid diagrams & technical workflow
│   ├── INTERVIEW_CHEATSHEET.md # 25 interview Q&A + 5 live modification drills
│   ├── AI_USAGE.md             # Transparent AI disclosure & debugging log
│   ├── LIMITATIONS.md          # Candid assessment of boundaries
│   └── AWS_DEPLOYMENT.md       # AWS Lambda (Mangum), S3, Bedrock guide
├── data/
│   └── ai_bi_assistant_sales_data_-_GET.csv # Sales dataset
├── Dockerfile                  # Containerized deployment
├── lambda_handler.py           # AWS Lambda Mangum entry point
├── Makefile                    # One-command build & test targets
└── requirements.txt            # Pinned dependencies
```

---

## 7. Framework Architecture & LangGraph / ADK Demo

### Running the LangGraph / ADK Adapter Demo
To demonstrate framework compliance with the JD (LangChain / LangGraph / Google ADK), an explicit state-machine adapter is included at `agents/langgraph_or_adk_demo.py`:
```bash
python3 agents/langgraph_or_adk_demo.py
```
This executes an explicit 4-node StateGraph pipeline:
`START -> [Plan & Route Node] -> [Query Node] -> [Verify Node] -> [Narrate Node] -> END`

### LangChain vs Google ADK vs Dify: Engineering Comparison
* **LangChain / LangGraph:** Best for complex Python/TS agent state machines with multi-step cycles, human-in-the-loop approvals, and custom memory graphs.
* **Google ADK (Agent Development Kit):** Focused on tight, native integration with Gemini models, multi-modal grounding, function calling, and Google Cloud Vertex AI infrastructure.
* **Dify:** A visual, enterprise-oriented orchestration platform suited for rapid graphical RAG pipeline prototyping, prompt management, and team collaboration.
* **Why Our Production Core Is Plain Python:** In high-reliability business intelligence, adding heavy abstractions creates hidden prompt loops, dependency bloat, and makes 60-second interview explanations difficult. Keeping the core orchestrator in plain Python ensures sub-millisecond execution, zero hidden state, and total auditability, while our `agents/langgraph_or_adk_demo.py` adapter proves framework mastery.

### Note on Repository Environment
The application is **100% pure Python** (`FastAPI`, `Pandas`, `SQLite`, `sqlglot`, `google-genai`). The `package.json` file in the root is used exclusively by containerized web hosting platforms (such as the Google AI Studio dev server runner) to start the web process via `npm run dev`. When copying to your standalone submission repository, only the Python files, `requirements.txt`, and `Makefile` are needed.

---

## 8. Automated Test Suite

Run all 30 automated tests:
```bash
python3 -m pytest -v
```

Output:
```
tests/test_api.py::test_api_health PASSED
tests/test_api.py::test_api_data_quality PASSED
tests/test_api.py::test_api_insights PASSED
tests/test_api.py::test_api_ask_total_revenue PASSED
tests/test_api.py::test_api_ask_driver_analysis PASSED
tests/test_api.py::test_api_ask_security_refusal PASSED
tests/test_drivers.py::test_driver_analysis_march_to_april PASSED
tests/test_drivers.py::test_driver_analysis_may_spike PASSED
tests/test_drivers.py::test_driver_analysis_june_drop PASSED
tests/test_etl.py::test_date_parsing_dd_mm_yyyy PASSED
tests/test_guard_security.py::test_guard_rejects_destructive_dml_and_ddl PASSED
tests/test_metrics_golden.py::test_golden_total_revenue PASSED
tests/test_metrics_golden.py::test_golden_top_product PASSED
tests/test_metrics_golden.py::test_verifier_blocks_corrupted_result PASSED
...
======================== 29 passed in 1.89s ========================
```

---

## 8. Interview Preparation Reference

Refer to **[`docs/INTERVIEW_CHEATSHEET.md`](docs/INTERVIEW_CHEATSHEET.md)** for:
* **25 High-Frequency Interview Questions** with crisp 60-second answers (Why SQLite, why sqlglot, what is Vectorless RAG vs Vector RAG, why the LLM never does math).
* **5 Live Modification Drills** with exact files and lines to modify on screen.
