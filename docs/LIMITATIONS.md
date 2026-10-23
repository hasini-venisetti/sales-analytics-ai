# System Limitations & Candid Scope Boundaries

In accordance with professional engineering standards, this document outlines what works, what does not work, and the rationale behind each technical boundary.

---

## 1. What Works (Fully Tested & Verified)

* **Certified Lane A Metrics:**
  - Total Net Revenue (₹14,39,200 default, ₹14,58,200 with returns).
  - Top Product ranking (Monitor at ₹4,73,000, Desk at ₹2,22,500, etc.).
  - Monthly trend series (Jan: ₹2.10L to peak May: ₹3.18L).
  - Regional rankings (South at ₹4,11,200).
  - Revenue change with driver analysis (March to April: +₹16,800 / +7.50%).
  - Average Order Value (₹29,983.33 across 48 clean orders).
  - Categories & Sales Channels breakdowns.
  - Returns value (₹19,000 across 1 order, TXN0033).
  - Discount impact (₹4,500 total, 0.31% of gross revenue).
* **Dual-Engine Verification:**
  - Every Lane A metric runs through both SQLite and an independent Pandas pipeline to verify arithmetic agreement.
* **Red-Team Security Guard:**
  - Rejects `DROP`, `DELETE`, `INSERT`, `UPDATE`, comments (`--`, `/* */`), stacked semicolons, and unknown columns.
* **Data Quality Audit & Quarantine:**
  - TXN0033 (returned), TXN0034 (quantity = 0), and TXN0051 (missing price) isolated into `sales_quarantine`.
* **Zero-Key Execution:**
  - Fully functional without any external LLM API key via the `RuleBasedProvider`.

---

## 2. What Does Not Work (By Design or Scope Constraints)

1. **Speculative Future Forecasting:**
   - *Example Query:* "Predict what our revenue will be next December."
   - *Why:* The dataset contains historical records from January to June 2026. Without time-series econometric models (ARIMA/Prophet) or external macro drivers, an LLM generating arbitrary future revenue figures would constitute hallucination. The system politely refuses and directs the user to historical trends.
2. **Arbitrary File Upload in UI:**
   - *Why:* The scope specifies analyzing `ai_bi_assistant_sales_data_-_GET.csv`. Dynamically accepting unseen schemas requires dynamic column mapping and dynamic metric registry generation, which exceeds a 3–4 hour scope.
3. **Multi-Turn Pronoun Resolution Across Distant Turns:**
   - *Example Query:* "And what about the other one from earlier?"
   - *Why:* We support immediate follow-ups based on the previous query parameters, but we do not maintain a persistent conversational graph across long sessions.
4. **Direct DDL / Administrative Operations:**
   - *Example Query:* "Create a new table for customers."
   - *Why:* The system is strictly a read-only analytics assistant. Administrative or modifying commands are permanently blocked by the AST SQL Guard.

---

## 3. Known Trade-Offs

* **SQLite File-Based Locking:**
  - While ideal for single-node deployments and fast local execution, SQLite does not support high-concurrency multi-master writes. For multi-tenant production systems, migration to PostgreSQL is recommended.
* **Vectorless RAG Keyword Coverage:**
  - Vectorless RAG is deterministic and requires 0 API keys, but relies on terms defined in `knowledge/glossary.json`. If a user uses an unmapped synonym (e.g., "boodle" for revenue), it routes to Lane B rather than Lane A.
