"""Snowflake SQL API adapter. No network call without explicit credentials."""
import os
from urllib.parse import urlparse
import httpx

class SnowflakeConfigurationError(RuntimeError):
    pass

def configuration():
    url = os.getenv("SNOWFLAKE_ACCOUNT_URL", "").rstrip("/")
    token = os.getenv("SNOWFLAKE_TOKEN", "")
    if not token or not url:
        raise SnowflakeConfigurationError("Set SNOWFLAKE_ACCOUNT_URL and SNOWFLAKE_TOKEN in your local environment")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".snowflakecomputing.com") or parsed.username or parsed.password or parsed.port or parsed.path:
        raise SnowflakeConfigurationError("Use an HTTPS Snowflake account hostname, not a Snowsight dashboard URL")
    return url, token

async def execute_statement(statement, *, bindings=None):
    """Execute a single allowlisted statement, return Snowflake's JSON result."""
    url, token = configuration()
    if statement not in {"SELECT CURRENT_VERSION()", "SELECT COUNT(*) FROM SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS",
                         "SELECT EVENT_ID, EVENT_TIME, SEVERITY, CATEGORY, SOURCE, DESCRIPTION FROM SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS ORDER BY EVENT_TIME DESC LIMIT 100"}:
        raise ValueError("Statement not on application allowlist")
    headers = {"Authorization": f"Bearer {token}", "X-Snowflake-Authorization-Token-Type": os.getenv("SNOWFLAKE_TOKEN_TYPE", "PROGRAMMATIC_ACCESS_TOKEN"), "Accept": "application/json", "Content-Type": "application/json", "User-Agent": "SnowflakeKemi/0.2"}
    payload = {"statement": statement, "timeout": 30}
    if bindings:
        payload["bindings"] = bindings
    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(url + "/api/v2/statements", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if response.status_code == 202 or (data.get("statementStatusUrl") and not data.get("data")):
            raise RuntimeError("Snowflake statement still running; asynchronous polling is not enabled in this prototype")
        return data

async def fetch_security_events():
    result = await execute_statement("SELECT EVENT_ID, EVENT_TIME, SEVERITY, CATEGORY, SOURCE, DESCRIPTION FROM SNOWFLAKE_KEMI.PUBLIC.SECURITY_EVENTS ORDER BY EVENT_TIME DESC LIMIT 100")
    columns = [column["name"].lower() for column in result.get("resultSetMetaData", {}).get("rowType", [])]
    return [dict(zip(columns, row)) for row in result.get("data", [])]
