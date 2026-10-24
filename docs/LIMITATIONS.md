# Known Limitations

I would rather be clear about what the project does not do than leave it for someone to discover.

## What works

- Loading the CSV, separating clean rows from problem rows, and recording the reason for each.
- All five example questions, with the SQL and the supporting figures shown.
- An explanation of what drove a change between two months.
- Independent cross-checking of the standard questions in Pandas.
- Refusal of destructive requests and of questions the data cannot answer.
- Running with no API key.
- Automated tests for data loading, the verified figures, question interpretation, the SQL guard, the driver analysis and the API.

## What is limited, and why

| Limitation | Why it exists |
|---|---|
| **The dataset is small.** There are 48 clean orders over six months, 8 a month. | That is the file I was given. Trends and rankings from so few orders are indicative, not statistically strong. |
| **Open-ended questions need a Gemini key.** Without one, only the standard question types are understood. | The rule-based interpreter recognises known shapes of question. It is reliable on those and cannot guess at new ones. |
| **The cross-check is strongest for standard questions.** | I can recompute my own queries independently. For SQL written by the model I validate and show it, but I cannot independently recompute every possible query. |
| **The model can misread a question.** | Language models sometimes do. That is why the interpretation is shown, the SQL is visible, and an unclear question is refused instead of guessed. |
| **Advice-style questions are not answered.** For example, "which products should I improve to increase sales?" | The app reports and explains what the data shows. Recommendations need judgement the data alone does not support, and I did not have time to build and test it. |
| **No forecasting.** | Six months of data cannot support a reliable prediction, so the app says so. |
| **No cost, margin or customer data.** | The file has none, so questions about profit or customers cannot be answered. |
| **Currency is assumed to be rupees.** | The file has no currency column. |
| **The order with a missing price is left out.** TXN0051, a Laptop Stand order in June, is not counted. | I will not invent a price. June revenue is therefore slightly understated. |
| **Returned orders are excluded from revenue by default.** | I treated a returned order as revenue that did not stay. It can be included with an option. |
| **Dates are read as day-month-year.** | That is what the file uses. A file in another format would be misread. |
| **One user at a time, no login, no rate limiting.** | This is a challenge project, not a production system. |
| **The database is rebuilt from the CSV every time the app starts.** | It keeps the project simple and consistent. It would not suit large or changing data. |
| **Not deployed to AWS.** | The design is in [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md). I did not deploy it. |
| **No automated pipeline yet.** | Tests are run by hand with `python -m pytest`. |

## Testing limits

The automated tests are designed to run without an API key, so they cover the rule-based path and the SQL guard. The live Gemini path needs a key and a connection, so it is checked by hand.

## What I would do next

See "What I would improve with another day of work" in [AI_USAGE.md](AI_USAGE.md).