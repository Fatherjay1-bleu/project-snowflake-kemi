import asyncio
import pytest
import httpx
from app.snowflake_sql import configuration, execute_statement, fetch_security_events, SnowflakeConfigurationError

def test_requires_credentials(monkeypatch):
    monkeypatch.delenv("SNOWFLAKE_TOKEN", raising=False)
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT_URL", "https://example.snowflakecomputing.com")
    with pytest.raises(SnowflakeConfigurationError):
        configuration()

def test_rejects_snowsight_url(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "fake")
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT_URL", "https://app.snowflake.com/jwbypgl/se58618")
    with pytest.raises(SnowflakeConfigurationError):
        configuration()

def test_rejects_arbitrary_sql():
    with pytest.raises((ValueError, SnowflakeConfigurationError)):
        asyncio.run(execute_statement("DROP DATABASE SNOWFLAKE_KEMI"))

def test_mocked_snowflake_api(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "fake-test-token")
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT_URL", "https://example.snowflakecomputing.com")
    def handler(request):
        assert request.url.path == "/api/v2/statements"
        assert request.headers["X-Snowflake-Authorization-Token-Type"] == "PROGRAMMATIC_ACCESS_TOKEN"
        return httpx.Response(200, json={"resultSetMetaData":{"rowType":[{"name":"EVENT_ID"},{"name":"SEVERITY"}]},"data":[["EVT-001","high"]]})
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    rows = asyncio.run(fetch_security_events())
    assert rows == [{"event_id":"EVT-001","severity":"high"}]
