import pytest
import json
from fastapi.testclient import TestClient

from agentkit.api.app import app

def test_api_daily_briefing_discovery():
    client = TestClient(app)
    
    # 1. Discover agent
    response = client.get("/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert any(a["agent_id"] == "daily_briefing" for a in agents)
    
    # 2. Get agent details
    response = client.get("/agents/daily_briefing")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "daily_briefing"
    assert "reporting" in data["capabilities"]

def test_api_daily_briefing_execution():
    client = TestClient(app)
    
    # Initialize DB tables for testing
    from agents.daily_briefing import get_db
    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS automation_health")
    conn.execute("DROP TABLE IF EXISTS leads")
    conn.execute("DROP TABLE IF EXISTS content_calendar")
    conn.execute("DROP TABLE IF EXISTS revenue")
    conn.execute("DROP TABLE IF EXISTS agent_activity")
    conn.execute("CREATE TABLE automation_health (id INTEGER PRIMARY KEY, status TEXT, uptime_pct REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY, score INTEGER, stage TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS content_calendar (id INTEGER PRIMARY KEY, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS revenue (id INTEGER PRIMARY KEY, amount REAL, status TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS agent_activity (action TEXT, target TEXT, status TEXT, details TEXT, agent_name TEXT DEFAULT 'daily_briefing', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()

    payload = {
        "input": json.dumps({})
    }
    
    # Requires only agent:execute_safe
    headers = {"Authorization": "Bearer test-token-safe"}
    response = client.post("/agents/daily_briefing/run", json=payload, headers=headers)
    assert response.status_code == 200
    result = response.json()
    
    assert result["agent_id"] == "daily_briefing"
    if result["status"] != "success":
        print("ERROR IN BRIEFING:", result)
    assert result["status"] == "success"
    
    output = result["output"]
    assert "result" in output
    assert "Automation Health" in output["result"] or "No agent activity" in output["result"]
