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
    return """<!doctype html><html><head><meta charset="utf-8"><title>Snowflake Cortex Intelligence</title>
<style>body{background:#0d1524;color:#eef4ff;font-family:system-ui;margin:0;padding:42px;max-width:930px}
h1{color:#63cef7}.panel{background:#19283d;border-radius:14px;padding:22px;margin:20px 0}
input,button{font:inherit;padding:11px;border-radius:7px}input{width:70%}button{background:#28b6ec;border:0;cursor:pointer}
pre{white-space:pre-wrap}</style></head><body><h1>❄ Snowflake Cortex Intelligence</h1>
<p>AI-assisted data intelligence prototype • Demo mode uses synthetic data.</p>
<div class="panel"><h2>Security event summary</h2><pre id="summary">Loading...</pre></div>
<div class="panel"><h2>Ask the analyst</h2><input id="question" placeholder="Summarize these security events">
<button onclick="ask()">Analyze</button><pre id="result"></pre></div>
<script>
fetch('/api/summary').then(r=>r.json()).then(j=>document.getElementById('summary').textContent=JSON.stringify(j,null,2));
async function ask(){const q=document.getElementById('question').value;const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});document.getElementById('result').textContent=JSON.stringify(await r.json(),null,2)}
</script></body></html>"""
