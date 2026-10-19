from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_summary():
    response = client.get("/api/summary")
    assert response.status_code == 200
    assert response.json()["total_events"] == 6

def test_events():
    response = client.get("/api/events")
    assert response.status_code == 200
    assert len(response.json()) == 6

def test_demo_ask(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_MODE", "demo")
    response = client.post("/api/ask", json={"question": "Summarize events"})
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
