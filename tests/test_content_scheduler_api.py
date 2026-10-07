import pytest
import json
from fastapi.testclient import TestClient

from agentkit.api.app import app

def test_api_content_scheduler_discovery():
    client = TestClient(app)
    
    # 1. Discover content_scheduler agent
    response = client.get("/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert any(a["agent_id"] == "content_scheduler" for a in agents)
    
    # 2. Get metadata
    response = client.get("/agents/content_scheduler")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "content_scheduler"
    assert "social_media_write" in data["required_permissions"]

def test_api_content_scheduler_generate_safe():
    client = TestClient(app)
    
    # Test action: generate
    payload_generate = {
        "input": json.dumps({
            "action": "generate",
            "pillar": "AI & Automation"
        })
    }
    headers = {"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/content_scheduler/run", json=payload_generate, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["output"]["result"]["action"] == "generate"
    assert "post" in result["output"]["result"]
    assert "AI" in result["output"]["result"]["post"] or "Automation" in result["output"]["result"]["post"] or "agents" in result["output"]["result"]["post"].lower()

def test_api_content_scheduler_schedule_week_dry_run():
    client = TestClient(app)
    
    # Test action: schedule_week with dry_run
    payload_schedule = {
        "input": json.dumps({
            "action": "schedule_week",
            "posts_per_day": 1,
            "dry_run": True
        })
    }
    headers = {"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/content_scheduler/run", json=payload_schedule, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    
    output = result["output"]["result"]
    assert output["action"] == "schedule_week"
    assert output["dry_run"] is True
    assert output["scheduled"] == 7
    assert len(output["posts"]) == 7
    # Verify the dummy result mapping logic from the patch
    for p in output["posts"]:
        assert p["result"]["status"] == "dry_run"
