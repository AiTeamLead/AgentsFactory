import pytest
import json
import os
import sqlite3
from fastapi.testclient import TestClient

from agentkit.api.app import app

def test_api_lead_loader_discovery():
    client = TestClient(app)
    
    # 1. Discover lead_loader agent
    response = client.get("/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert any(a["agent_id"] == "lead_loader" for a in agents)
    
    # 2. Get lead_loader metadata
    response = client.get("/agents/lead_loader")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "lead_loader"
    assert "lead_management" in data["capabilities"]

def test_api_lead_loader_safe_execution(tmp_path):
    client = TestClient(app)
    
    # Test dry_run
    payload_dry = {
        "input": json.dumps({
            "dry_run": True
        })
    }
    headers={"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/lead_loader/run", json=payload_dry, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["output"]["result"]["dry_run"] is True

    # Test isolated DB test
    test_db = str(tmp_path / "test_metrics.db")
    payload_test_db = {
        "input": json.dumps({
            "download": True,
            "dry_run": False
        })
    }
    
    os.environ["LEAD_LOADER_DB_PATH"] = test_db
    headers={"Authorization": "Bearer test-token-admin"}
    response = client.post("/agents/lead_loader/run", json=payload_test_db, headers=headers)
    del os.environ["LEAD_LOADER_DB_PATH"]
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    
    output = result["output"]["result"]
    assert "total_inserted" in output
    assert output["total_inserted"] >= 0
    
    # Verify the test DB was created and schema is valid
    assert os.path.exists(test_db)
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    # Check if social_lead_score exists (the issue from Phase 1)
    cursor.execute("PRAGMA table_info(leads)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "social_lead_score" in columns
    conn.close()
