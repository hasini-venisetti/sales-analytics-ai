# How I Used AI

## Which AI tools I used

- **Claude** for planning, for writing the detailed build instructions I gave to the coding agent, for reviewing the agent's plan and results, and for helping write these documents.
- **Antigravity**, Google's agentic coding environment, running a Gemini Flash model. It generated the code and the tests.
- **Gemini API** inside the application itself, as an optional model for open-ended questions. The app works without it.
- **Pandas**, which I used to check the agent's numbers independently of the app.

## How I used AI during development

I did not start by asking the agent to build an app. I started with the data.

1. **Read the brief and profiled the CSV first.** Before any code, I loaded the file in Pandas and looked for problems. That is how I found the three rows that needed special handling: a returned order (TXN0033), an order with quantity 0 (TXN0034) and an order with no unit price (TXN0051). I also confirmed the dates are day-month-year.
2. **Decided what the app should be.** I worked out what the company is evaluating (correct answers, safe handling of AI output, clear explanations) and chose a design around one rule: the AI never produces a number, the database does.
3. **Wrote a detailed brief for the coding agent.** It covered the data problems, the revenue definition, the answers I expected, the safety rules, the tests and the documentation.
4. **Asked the agent for a plan before any code.** I reviewed it and approved it with changes (below).
5. **Let the agent build in milestones**, starting with data loading and the standard questions, then the API, the SQL guard, the driver analysis and the interface.
6. **Reviewed the result** against the brief and checked the numbers myself.

## Problems I encountered

1. **The plan included an extra Node server.** The agent proposed a Node/Express proxy for its preview environment. The task is a Python application, so I asked for it to be removed and for FastAPI to serve the page directly. A stray `package.json` also appeared and I removed it.
2. **The plan would generate data if the CSV was missing.** I did not accept this. An app that invents sales data is worse than one that stops. It now loads the real file or exits with a clear error.
3. **A mismatch in the number of valid rows.** My brief said 49 valid rows and the agent built 48. I traced it to my own count, which included the quantity-0 order. With the rule "completed, quantity above zero, price present", the correct number is 48. The revenue total is the same either way, because the zero-quantity order contributes nothing.
4. **A rounded figure written as text.** The Monitor share of revenue appeared as 32.8%. The actual value is 32.87%, which rounds to 32.9%. I asked for percentages to be calculated in code and not typed into text.

## How I debugged them

- For each problem I compared the app's output with my own Pandas calculation on the raw CSV, and looked for where the two first disagreed.
- For the row count, I listed the rows that fail each rule (3 in total, 1 returned, 1 with quantity 0, 1 with no price) and counted what was left: 51 minus 3 is 48.
- For the percentage, I divided the Monitor total by the overall total (473,000 / 14,39,200) and compared it with what the page showed.
- After each change I re-ran the test suite.

## What I would improve with another day of work

- Add a GitHub Actions workflow so the tests run on every push.
- Deploy the app to AWS and put a live link in the README. The design is in [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md), but it is not deployed.
- Load the CSV from S3 instead of a local file.
- Add questions that give advice, such as which products to focus on, using only figures computed from the data.
- Offer an optional, clearly labelled estimate for the order with the missing price, instead of leaving it out entirely.
- Test the Gemini path against a larger set of real questions and measure how often the SQL guard rejects a query.
- Express the pipeline in LangGraph or Google ADK as a comparison with the plain Python version.
- Add authentication and rate limiting before any public use.