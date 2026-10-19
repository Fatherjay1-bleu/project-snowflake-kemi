import csv
import os
from collections import Counter
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Snowflake Cortex Intelligence", version="0.1.0")
EVENTS = Path(__file__).resolve().parent.parent / "sample_data" / "events.csv"

class AskRequest(BaseModel):
    question: str

def read_events():
    with EVENTS.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

async def cortex_complete(question: str):
    account = os.getenv("SNOWFLAKE_ACCOUNT_URL", "").rstrip("/")
    token = os.getenv("SNOWFLAKE_TOKEN", "")
    model = os.getenv("SNOWFLAKE_MODEL", "llama3.1-70b")
    if not account.startswith("https://") or not token:
        raise HTTPException(status_code=503, detail="Snowflake connection is not configured")
    url = f"{account}/api/v2/cortex/inference:complete"
    payload = {"model": model, "messages": [{"role": "user", "content": question}], "stream": False}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Snowflake returned HTTP {exc.response.status_code}") from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not complete Snowflake request") from exc

@app.get("/health")
def health():
    return {"status": "ok", "mode": os.getenv("SNOWFLAKE_MODE", "demo")}

@app.get("/api/events")
def events():
    return read_events()

@app.get("/api/summary")
def summary():
    items = read_events()
    return {"total_events": len(items), "by_severity": dict(Counter(item["severity"] for item in items)), "by_category": dict(Counter(item["category"] for item in items))}

@app.post("/api/ask")
async def ask(body: AskRequest):
    mode = os.getenv("SNOWFLAKE_MODE", "demo").lower()
    if mode == "live":
        return {"mode": "live", "result": await cortex_complete(body.question)}
    if mode == "demo":
        stats = summary()
        return {"mode": "demo", "answer": f"Demo data contains {stats['total_events']} events. Severity breakdown: {stats['by_severity']}. Live LLM analysis requires Snowflake credentials."}
    raise HTTPException(status_code=500, detail="Invalid SNOWFLAKE_MODE")

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return (Path(__file__).resolve().parent / "dashboard.html").read_text(encoding="utf-8")


@app.get("/api/snowflake/status")
def snowflake_status():
    """Configuration state only; does not reveal or validate credentials."""
    from app.snowflake_sql import configuration, SnowflakeConfigurationError
    try:
        configuration()
        return {"configured": True, "connected": False, "note": "Credentials present; use /api/snowflake/events to verify connectivity"}
    except SnowflakeConfigurationError:
        return {"configured": False, "connected": False, "note": "Set Snowflake account URL and token privately"}

@app.get("/api/snowflake/events")
async def snowflake_events():
    """Read actual events via Snowflake SQL API when explicitly configured."""
    from app.snowflake_sql import fetch_security_events, SnowflakeConfigurationError
    try:
        rows = await fetch_security_events()
        return {"source": "snowflake_sql_api", "events": rows, "count": len(rows)}
    except SnowflakeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail="Snowflake query failed or is still running") from exc
