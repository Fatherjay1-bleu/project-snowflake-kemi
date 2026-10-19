# Snowflake Kemi: actual Snowflake SQL integration

The local dashboard is useful without credentials. To demonstrate **real Snowflake use**, open a worksheet in Snowsight and execute `sql/setup.sql`. This creates the `SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS` table with synthetic events.

Create a least-privilege integration role and an OAuth token or programmatic access token authorized for the SQL API. A PAT may require a Snowflake network policy. Do not paste tokens into ChatGPT, GitHub, or screenshots.

Set these environment variables on your own machine or deployment platform:
- `SNOWFLAKE_ACCOUNT_URL=https://<org>-<account>.snowflakecomputing.com` (not `app.snowflake.com`)
- `SNOWFLAKE_TOKEN=<secret>`
- `SNOWFLAKE_TOKEN_TYPE=PROGRAMMATIC_ACCESS_TOKEN` (or `OAUTH`)
- `SNOWFLAKE_MODE=demo` until you explicitly enable a live mode

The Python adapter in `app/snowflake_sql.py` uses Snowflake's **SQL API v2** (`POST /api/v2/statements`) and an allowlist of read-only SQL statements. It intentionally rejects arbitrary SQL. This adapter is not automatically activated by demo mode. Its network behavior is tested using a mocked HTTP transport, **not** a live Snowflake account.

For a real integration check, configure the variables locally, then run:
`python -c "import asyncio; from app.snowflake_sql import fetch_security_events; print(asyncio.run(fetch_security_events()))"`

Requires a running warehouse with appropriate permissions. Review trial credits and suspend warehouses after testing.

Docs: https://docs.snowflake.com/en/developer-guide/sql-api
