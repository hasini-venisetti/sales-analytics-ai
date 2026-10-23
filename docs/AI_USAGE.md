# AI Usage Disclosure & Engineering Log

> **Note for the Candidate:** This document is designed to be completely honest and transparent about how AI was used. Review each section, especially the marked `[EDIT ME: ...]` sections, and add your personal reflections and authentic voice before your interview.

---

## 1. Which AI Tools I Used

* **Google AI Studio / Gemini Models (gemini-3.8-flash):** Used as an interactive pair-programmer to plan architecture, verify math against the CSV, draft boilerplate FastAPI/Pydantic code, and generate unit tests.
* **Modern `@google/genai` Python SDK:** Integrated into the application's Lane B (`app/llm/gemini.py`) to generate Text-to-SQL for open-ended queries.
* *[EDIT ME: Mention any other AI tools you used, e.g. Claude, ChatGPT, GitHub Copilot, Cursor, etc. If none, write: "Only Google AI Studio & Gemini were used."]*

---

## 2. How I Used AI During Development

* **Data Profiling & Mathematical Verification:**
  - I used AI to inspect the 51-row dataset structure and verify edge cases:
    - `TXN0033` (Returned status, ₹19,000 gross)
    - `TXN0034` (Quantity = 0, invalid completed order)
    - `TXN0051` (Missing `Unit_price`)
  - We confirmed that excluding all 3 dirty/returned rows leaves exactly **48 clean completed rows**, producing a total net revenue of **₹14,39,200**.
* **Architecture & Reliability Strategy:**
  - Formulated the core thesis: *"The LLM never does arithmetic. It only classifies intent or drafts SQL. All math is performed by SQLite and cross-checked by an independent Pandas verifier."*
  - Designed the 3-Lane router (Lane A: Deterministic templates; Lane B: Guarded Text-to-SQL; Lane C: Polite refusal).
* **AST Security Guardrails:**
  - Co-designed `SQLGuard` with `sqlglot` to parse incoming SQL into an Abstract Syntax Tree, enforcing single `SELECT` statements, row caps, and column/table allowlists.
* *[EDIT ME: Add 1-2 sentences on how you specifically prompted the AI or guided the development workflow in your own words.]*

---

## 3. Problems I Encountered

* **The 49 vs 48 Row Trap:**
  - My initial manual count assumed 49 valid rows. When auditing row-by-row in code, we discovered that `TXN0034` had `Quantity = 0`. Since our business filter enforces `Quantity > 0`, the correct clean completed row count is exactly 48 rows. The total revenue (₹14,39,200) was unaffected, but the row count needed correction.
* **Model Deprecation During Integration:**
  - When calling Gemini in Python, the older model alias returned a `404 NOT_FOUND` indicating it was retired. We updated the model to `gemini-3.8-flash`, which resolved the issue and produced fast, accurate SQL.
* *[EDIT ME: Describe any other problem or unexpected behavior you ran into while testing or running the code locally.]*

---

## 4. How I Debugged Them

* **Data Scope Alignment:**
  - Audited the Pandas filter `df[(df['Status'] == 'Completed') & (df['Quantity'] > 0) & (df['Unit_price'].notna())]` and verified that 51 total rows minus 3 quarantined rows equals 48 rows. Updated all documentation and tests to reflect this exact baseline.
* **Direct Model Verification:**
  - Added an automated live test in `tests/test_gemini_live.py` that verifies `GeminiProvider` directly with `gemini-3.8-flash` and ensures output passes through `SQLGuard`.
* *[EDIT ME: Add your personal debugging technique, e.g. "I ran pytest with -v flag", "I inspected the SQLite database directly", etc.]*

---

## 5. What I'd Improve with Another Day

* [ ] Add dynamic CSV file upload in the UI with automated schema profiling and quarantine logging.
* [ ] Implement conversational multi-turn session persistence using SQLite or Redis.
* [ ] Add automated webhook notifications (Slack/Teams) on anomaly detection or peak volume spikes.
* *[EDIT ME: Add 1 thing you personally find exciting that you'd love to build if this were a production project.]*
