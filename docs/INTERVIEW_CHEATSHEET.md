# Interview Cheatsheet: Ask-the-Numbers
> Designed for RSG Graduate Engineer Trainee (Python with GenAI) Interview & Live Modification Defense.

---

## Part 1: 25 High-Frequency Technical & GenAI Questions (60-Second Answers)

### 1. What is the central design philosophy of Ask-the-Numbers?
**Answer:** "The LLM never does arithmetic. LLMs are probabilistic token predictors, not calculators. The LLM's role is strictly intent classification and SQL drafting. Every number originates from a validated query against SQLite, is cross-checked by an independent Pandas verifier, and is displayed with a transparent audit proof panel."

### 2. Why did you use SQLite instead of PostgreSQL or MySQL?
**Answer:** "For an offline or single-node embedded analytics scope, SQLite requires zero external server setup, runs in-process with sub-millisecond query latency, supports full ANSI SQL with Window functions and CTEs, and provides read-only connection isolation. When scaling, the queries and schema map directly to PostgreSQL."

### 3. What is Vectorless RAG, and why did you use it here instead of Vector Embeddings?
**Answer:** "Vectorless RAG uses structured, hierarchical symbol indexing (domain → entity → synonyms → canonical metric) rather than dense vector embeddings. In structured tabular domains with exact business definitions (e.g. 'sales' = net revenue = Qty×Price − Discount), embeddings suffer from drift, threshold tuning, and non-determinism. Vectorless RAG is deterministic, zero-latency, auditable, and requires zero API keys."

### 4. When would you switch to Vector RAG?
**Answer:** "I would switch to vector RAG when searching unstructured documents, user manuals, policy PDFs, or fuzzy narrative transcripts where keyword taxonomies cannot cover semantic variety."

### 5. How does the Three-Lane Router work?
**Answer:** "Lane A handles certified, recurring executive questions using pre-compiled parameterized SQL templates (100% deterministic). Lane B handles open-ended questions where the LLM drafts SQL, which must pass an AST security guard before execution. Lane C politely refuses out-of-scope, destructive, or future forecasting questions with helpful alternatives."

### 6. How does SQL Guard prevent SQL Injection?
**Answer:** "We use `sqlglot` to parse the raw query into an Abstract Syntax Tree (AST). We enforce that: 1) There is exactly one statement; 2) The root node is a `SELECT` statement; 3) Tables and columns exist in strict allowlists; 4) Comments (`--`, `/* */`) and semicolons are rejected; 5) A `LIMIT 500` is enforced; 6) The connection is read-only."

### 7. What is Dual-Engine Verification?
**Answer:** "Whenever a query executes, a second independent calculator (a Pandas pipeline reading the raw CSV directly) independently recomputes the expected answer. Only if both engines agree within 0.01 tolerance is the answer marked Verified. If they diverge, the answer is blocked."

### 8. What dirty rows were planted in the dataset and how did you handle them?
**Answer:** "There are three planted rows in the 51-row dataset:
1. `TXN0033`: A Returned order (Monitor, ₹19,000 value). Excluded from default revenue, tracked in Returns Value.
2. `TXN0034`: Quantity = 0. Quarantined as an invalid zero-value order.
3. `TXN0051`: Missing `Unit_price`. Quarantined with an audit note; we never silently invent or impute prices.
Quarantined rows are saved in `sales_quarantine`, while verified metrics query `v_sales_valid` (48 rows)."

### 9. Why does default scope have 48 rows instead of 49 or 51?
**Answer:** "The CSV has 51 rows. Row TXN0033 is `Returned` (1 row), row TXN0034 has `Quantity=0` (1 row), and row TXN0051 has missing `Unit_price` (1 row). 51 − 3 = 48 valid completed transactions. If returned orders are opted in by the user, valid rows become 49."

### 10. What is the total net revenue and how is it calculated?
**Answer:** "Total net revenue is **₹14,39,200**. Formula: `SUM((Quantity * Unit_price) - Discount_amount)` on completed valid orders. Total gross revenue is ₹14,43,700 with ₹4,500 in total discounts."

### 11. Which product is the top performer?
**Answer:** "The Monitor, generating **₹4,73,000** in net revenue across 50 units. It represents ~32.9% of company revenue, indicating a product concentration risk."

### 12. Which region is the top performer?
**Answer:** "The South region, generating **₹4,11,200** in net revenue, followed by North (₹3,84,450), East (₹3,46,700), and West (₹2,96,850)."

### 13. How did revenue change between March and April 2026?
**Answer:** "Net revenue increased by **+₹16,800 (+7.50%)**, growing from ₹2,23,900 in March to ₹2,40,700 in April. Primary growth was driven by Wireless Mouse (+₹22,100) and USB-C Hub (+₹14,400)."

### 14. Why did revenue spike in May 2026?
**Answer:** "May was our peak revenue month at **₹3,18,500** (+32.32% MoM). The surge was driven by a surge in Monitor sales (+₹57,500) and Office Chair sales (+₹15,600), especially in the West region."

### 15. Why did revenue drop in June 2026?
**Answer:** "June dropped by **-₹1,07,250 (-33.67%)** to ₹2,11,250. This was caused by a sharp pullback in Monitor orders (-₹66,500) and Desk orders (-₹25,000) across West and East."

### 16. What is Agentic AI in the context of this project?
**Answer:** "An autonomous agent plans, invokes tools, decomposes tasks, and reflects on results. In our `DriverAnalysisAgent`, the agent takes a question like 'How did revenue change?', devises a 4-step decomposition plan (Aggregate → Product Variance → Regional Variance → Channel Variance), executes the queries, and synthesizes an executive briefing."

### 17. How does LangChain compare to Google ADK and Dify?
**Answer:** "LangChain/LangGraph provides a modular Python/TS framework for chaining agents and graph-based state transitions. Google ADK (Agent Development Kit) focuses on native Gemini tool-use and grounding patterns. Dify is an enterprise visual orchestration platform for visual workflow building and RAG pipelines."

### 18. How do you prevent LLM hallucination in narrative generation?
**Answer:** "We use a regex Number Audit: after generating narrative text, our system checks that every number in the narrative exists in the database query result set. If an ungrounded figure appears, the system reverts to an exact template."

### 19. How does the application operate with ZERO API keys?
**Answer:** "The system implements a pluggable `LLMProvider` interface. If `GEMINI_API_KEY` is absent, the router defaults to `RuleBasedProvider`, which parses questions via regex, n-grams, and the vectorless glossary. All core and golden metrics work without spending an API cent."

### 20. How are dates handled?
**Answer:** "Dates in the raw CSV use `dd-mm-yyyy`. Pandas and SQLite ETL explicitly use `format='%d-%m-%Y'` to avoid date-month inversion (e.g. 03-01-2026 is Jan 3, not Mar 1). They are indexed in SQLite as ISO `YYYY-MM-DD` and `order_month` (`YYYY-MM`)."

### 21. How is thread safety ensured with SQLite?
**Answer:** "SQLite connections in Python should not be shared across threads. We use a thread-safe connection pattern (`get_db_connection()` per request/thread) or context managers, preventing `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`."

### 22. How would you deploy this to AWS?
**Answer:** "1) API: Package FastAPI with `Mangum` in AWS Lambda behind API Gateway or run in AWS App Runner / ECS; 2) Data: Store CSVs in S3 and load to RDS PostgreSQL or Athena; 3) LLM: Switch provider to AWS Bedrock (Claude or Titan) or SageMaker endpoint."

### 23. What is the Average Order Value (AOV)?
**Answer:** "AOV is **₹29,983.33** across the 48 completed transactions (₹14,39,200 ÷ 48)."

### 24. What is the total discount given and its business impact?
**Answer:** "Total discounts granted amount to **₹4,500**, which is **0.31%** of total gross revenue (₹14,43,700), indicating minimal margin dilution."

### 25. What would you do with another 24 hours?
**Answer:** "I would add: 1) Live CSV upload and schema inference for any arbitrary sales file; 2) Natural language conversational memory with session state persistence; 3) Automated Slack/Teams webhook alert delivery on anomaly detection."

### 26. What is the Trust Meter and how is its score calculated?
**Answer:** "Every answer receives an auditable 0–100 reliability score based on 4 transparent factors: 1) Dual-engine verification check (+35 pts); 2) Query execution lane (Deterministic Lane A: 0 penalty vs Guarded LLM: -10 pts); 3) Quarantined rows ratio (-2 pts per isolated dirty row); 4) Zero silent imputation policy (+10 pts). Refused queries get 0. An answer with Trust 96 proves that numbers were independently verified, deterministically generated, and transparent about exclusions."

### 27. What is "Challenge this answer" (Definition Sensitivity)?
**Answer:** "Revenue is an accounting definition, not a physical fact. One click re-runs the query under 4 alternative scopes: Default Net Revenue (₹14.39L), Gross Merchandise Value without discounts (₹14.43L), Returns Included (₹14.58L), and Imputed Missing Price (₹14.45L). Crucially, the system checks whether the core business conclusions change: Monitor remains #1 product and South remains #1 region across all 4 definitions with <2% total variance, proving management decisions are stable."

### 28. What does the live "Break It" demo show?
**Answer:** "With one click in the UI, a battery of 5 live attacks is fired at the backend: 1) Destructive `DROP TABLE`; 2) Stacked semicolons (`SELECT; DELETE`); 3) SQL comment injection (`-- bypass limit`); 4) Hallucinated columns (`customer_ssn`); 5) System prompt jailbreaks. The UI displays each attack being intercepted in real-time by the AST Guard with 0% vulnerability rate in <10ms."

### 29. What is "Advisor with Evidence"?
**Answer:** "Most BI assistants either output raw numbers or output ungrounded LLM advice. Our Advisor strictly separates three tiers: 1) Mathematically Verified Facts (quoted verbatim from SQLite); 2) Identified Risks & Trajectory (analytical observations like Monitor's 32.9% concentration share); 3) Actionable Strategic Recommendations (bundling laptop stands with monitors, regional distributor incentives). This guarantees strategic advice without corrupting ground truth."

---

## Part 2: 5 Live Modification Drills (Files & Exact Lines)

If the interviewer says: *"Can you change this live right now?"* — here is your exact cheat sheet:

### Drill 1: Add a new metric "Profit" (assuming 30% margin)
* **File to touch:** `app/core/metrics.py` and `app/data/etl.py`
* **Change:** Add `profit = net_revenue * 0.30` to `metrics.py` definitions and create a query template in `app/core/lane_a.py`.

### Drill 2: Change default revenue to INCLUDE returned orders
* **File to touch:** `app/data/etl.py`
* **Line:** In view `v_sales_valid`, remove `AND status = 'Completed'` so it queries `v_sales_with_returns`. Total revenue becomes ₹14,58,200.

### Drill 3: Add a new product synonym or business term
* **File to touch:** `app/knowledge/glossary.json`
* **Action:** Add `"screen"` or `"telly"` under `products.Monitor`, or `"income"` under `metrics.revenue.synonyms`. Vectorless RAG will instantly pick it up.

### Drill 4: Change SQL row limit from 500 to 100
* **File to touch:** `app/core/guard.py`
* **Line ~65:** Change `ast = ast.limit(500)` to `ast = ast.limit(100)`.

### Drill 5: Add a new question type to Lane A (e.g. "orders by channel")
* **File to touch:** `app/core/lane_a.py`
* **Action:** Add `"orders_by_channel"` into `TEMPLATES`:
  ```python
  "orders_by_channel": {
      "sql": "SELECT sales_channel, COUNT(*) AS orders FROM {view} GROUP BY sales_channel;",
      "formula": "COUNT(*) GROUP BY Sales_channel",
      "chart_type": "bar"
  }
  ```
  and add `"orders by channel"` match in `app/llm/rule_based.py`.
