# Ask-the-Numbers: A Mini AI Business Intelligence Assistant

I built this for RSG's AI-Assisted Development Challenge. You type a question about the sales data in plain English, and the app answers it with a number you can check. Every answer comes with the exact SQL that produced it, the rows behind it, and a note on which records were left out and why.

The idea I kept coming back to while building it: **the AI never does the maths.** It only helps work out what you are asking. Every figure comes from a database query, and a second, independent calculation in Pandas has to agree before the answer is marked Verified.

![Home page of the app](docs/images/01-home.png)
*The home page, with example questions and the mode badge (Rule-based or Gemini).*

## What it does

- Loads the sales CSV into SQLite and separates clean rows from problem rows.
- Answers the five challenge questions: total revenue, top product, monthly trend, top region, and revenue change between two months.
- Explains what drove a change between two months (by product, region and channel).
- Shows the SQL, the result table, the formula and the assumptions behind each answer.
- Refuses destructive or unsupported requests and says why.
- Runs with no API key. If a Gemini key is set, it also handles open-ended questions through guarded text-to-SQL.

## Run it

You need Python 3.11 or newer.

**Windows (PowerShell)**
```
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

**Mac / Linux**
```
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Then open http://localhost:8000. The CSV is read from `data/ai_bi_assistant_sales_data_-_GET.csv`. If that file is missing, the app stops with a clear error. It never invents data.

**Optional: turn on Gemini.** Set these environment variables (or put them in a `.env` file) before starting:
```
GEMINI_API_KEY=your-key
LLM_MODEL=the-gemini-model-name-you-want-to-use
```
Without a key the app uses its built-in rule-based interpreter. The badge at the top of the page shows which mode is active.

**Run the tests**
```
python -m pytest -v
```

![Tests passing](docs/images/11-tests-passing.png)
*All automated tests passing.*

## Questions to try, and the answers I verified by hand

I checked these against the CSV with Pandas, independently of the app.

| Question | Answer |
|---|---|
| What is the total revenue? | ₹14,39,200 |
| Which product generated the highest revenue? | Monitor, ₹4,73,000 |
| What is the monthly revenue trend? | Jan ₹2,10,250, Feb ₹2,34,600, Mar ₹2,23,900, Apr ₹2,40,700, May ₹3,18,500, Jun ₹2,11,250 |
| Which region generated the highest sales? | South, ₹4,11,200 |
| How did revenue change between March and April? | Up ₹16,800 (+7.50%) |

![Total revenue answer](docs/images/02-total-revenue.png)
*Total revenue answer with the Verified badge.*

![Top product answer](docs/images/03-top-product.png)
*Top product answer with the ranking table.*

![Monthly trend chart](docs/images/04-monthly-trend.png)
*Monthly revenue trend chart.*

![Top region answer](docs/images/05-top-region.png)
*Top region answer with the supporting figures.*

![Month-to-month change with drivers](docs/images/06-month-change.png)
*March to April change, with the products that drove it.*

## What is in an answer

![SQL and proof panel](docs/images/07-proof-panel.png)
*The SQL tab and the proof panel: the query, the formula, the assumptions and the row counts.*

![Data quality tab](docs/images/08-data-quality.png)
*The data quality tab, listing the rows I set aside and the reason for each.*

## API

The backend is FastAPI. Interactive documentation is at http://localhost:8000/docs.

| Endpoint | Purpose |
|---|---|
| `POST /api/ask` | Takes a question, returns the answer, the SQL, the supporting rows and whether it was verified |
| `GET /api/data-quality` | Lists loaded rows, excluded rows and the reasons |
| `GET /api/insights` | Headline insights computed from the data |
| `GET /api/schema` | Describes the tables and columns |

Example:
```
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total revenue?"}'
```

![Swagger API docs](docs/images/12-api-docs.png)
*The automatic API documentation.*

## How the data is stored and queried

The CSV has 51 rows. On startup the loader parses the dates (they are day-month-year), checks every row, and puts each one in exactly one place: 48 clean rows go into the sales table, and 3 problem rows go into a quarantine table with a reason. All questions read from a view called `v_sales_valid`, so dirty rows cannot leak into the numbers. The full explanation is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## How I prevent wrong or unsupported answers

- The AI never writes a number. Figures come from SQL, and the same figure is recomputed independently in Pandas.
- Generated SQL is parsed and must be a single read-only SELECT on approved tables and columns, and it runs on a read-only connection with a row limit.
- The narrator's text is checked so that every number it mentions appears in the query result.
- Questions the data cannot answer are refused with an explanation instead of guessed.

## Project structure

```
app/
  config.py            settings and paths
  main.py, __main__.py app entry points
  api/                 routes and request/response models
  core/
    orchestrator.py    runs a question through the steps
    lane_a.py          certified SQL for the standard questions
    guard.py           SQL validation for generated queries
    verifier.py        independent Pandas cross-check
    agent_drivers.py   explains what drove a change
    narrator.py        writes the answer text and audits its numbers
    vectorless_rag.py  glossary lookup without embeddings
    metrics.py         metric definitions
  data/
    etl.py             CSV loading and cleaning
    quality.py         data quality report
  llm/
    rule_based.py      works with no key
    gemini.py          used when a key is set
  knowledge/glossary.json
  static/              the web page
tests/
docs/
lambda_handler.py
Dockerfile
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [How I used AI](docs/AI_USAGE.md)
- [AWS deployment](docs/AWS_DEPLOYMENT.md)
- [Known limitations](docs/LIMITATIONS.md)

## Challenge requirements and where I met them

| Requirement | Where |
|---|---|
| Load CSV into a database | `app/data/etl.py`, SQLite |
| Handle missing or invalid records | Quarantine table, [Architecture](docs/ARCHITECTURE.md#data-layer) |
| Explain storage and querying | [Architecture](docs/ARCHITECTURE.md#data-layer) |
| API that accepts a question | `POST /api/ask` |
| Handle invalid requests and errors | Input validation and a consistent error response |
| Support at least four of five questions | All five are supported |
| Deterministic calculations and supporting figures | Parameterised SQL, proof panel |
| LLM or AI-assisted interpretation | Rule-based interpreter and Gemini |
| Validate generated SQL, no destructive operations | `app/core/guard.py`, read-only connection |
| Explain how wrong answers are prevented | Section above and [Architecture](docs/ARCHITECTURE.md#how-wrong-answers-are-prevented) |
| Simple interface | `app/static/` |
| At least five tests covering valid, invalid and edge cases | `tests/` |
| Known limitations | [Limitations](docs/LIMITATIONS.md) |
| AI usage document | [AI usage](docs/AI_USAGE.md) |