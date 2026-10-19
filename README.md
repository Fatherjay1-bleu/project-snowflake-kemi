# Project Snowflake Kemi

Snowflake Cortex Intelligence — FastAPI data intelligence demonstration for the MLH Best Use of Snowflake challenge.

## Features
- Local demo mode using synthetic security events
- Dashboard and severity analytics
- Snowflake Cortex REST inference integration (requires your own credentials)
- Automated API tests

## Local start
```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

Copy `.env.example` to `.env` and configure environment variables for optional live mode. Never commit `.env`, tokens or credentials.

Run tests with `pytest -q`.

**Status:** Starter prototype; live Snowflake integration and production deployment not yet verified.
