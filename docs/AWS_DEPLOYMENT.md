# AWS Cloud Deployment Architecture (Designed & Lambda-Ready)

This document outlines how **Ask-the-Numbers** is architected for seamless deployment to Amazon Web Services (AWS), aligning directly with the Graduate Engineer Trainee job description.

---

## 1. Serverless Architecture Overview

```
                      +-------------------+
                      |   Amazon S3       |
                      | (Sales CSVs / DB) |
                      +---------+---------+
                                |
                                v
User Request ---> Amazon API Gateway ---> AWS Lambda (FastAPI + Mangum)
                                                |
                               +----------------+----------------+
                               |                                 |
                               v                                 v
                     Amazon Bedrock / SageMaker       CloudWatch Logs & Metrics
                     (LLM for Lane B SQL drafting)   (Structured Request Tracing)
```

---

## 2. Component Specifications

### A. Compute: AWS Lambda + Mangum (`lambda_handler.py`)
* The entire FastAPI application is wrapped using `Mangum` (`lambda_handler.py`).
* Runs as a containerized Lambda function using our provided `Dockerfile` or a Python 3.11 zip deployment package.
* **Benefits:** Scale-to-zero cost efficiency, zero server maintenance, handles sudden traffic spikes automatically.

### B. Storage: Amazon S3
* In a cloud workflow, raw sales data files are uploaded to an S3 bucket (e.g., `s3://company-bi-data/sales/`).
* S3 Event Notifications trigger Lambda to execute the ETL pipeline (`app/data/etl.py`) to validate and rebuild the analytics database.

### C. LLM Backend: Amazon Bedrock or SageMaker
* For enterprise compliance where external third-party API calls are restricted, the `LLMProvider` can connect directly to **Amazon Bedrock** (e.g. Claude 3.5 Sonnet / Amazon Titan) or an internal **Amazon SageMaker JumpStart** endpoint.

### D. Chat Front-End: Amazon Lex (Optional)
* Amazon Lex can be configured as a voice/text conversational front-end that routes intents directly to the FastAPI API Gateway endpoint.

---

## 3. Local vs Cloud Cost Comparison

| Component | AWS Equivalent | Estimated Monthly Cost (Low-Volume) |
|---|---|---|
| In-Process SQLite | Amazon Aurora Serverless / RDS PostgreSQL | ~$0.00 – $15.00 / month |
| FastAPI Server | AWS Lambda + API Gateway | Free Tier eligible (< 1M requests) |
| Local CSV | Amazon S3 Standard | < $0.05 / month |
| Gemini Flash | Amazon Bedrock (Pay-per-token) | ~$0.50 – $2.00 / month |
| **Total** | | **<$20 / month** |
