import pytest
import json
import os
from fastapi.testclient import TestClient
from agentkit.api.app import app

def test_api_database_path_traversal_blocked():
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token-db"}
    
    # 2. ../ path traversal attempt
    payload = {"input": json.dumps({"test_db_path": "../../sensitive.db", "dry_run": False})}
    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "failure"

def test_api_absolute_path_blocked():
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token-db"}
    
    # 3. absolute path attempt
    payload = {"input": json.dumps({"test_db_path": "/etc/passwd.db", "dry_run": False})}
    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "failure"

def test_api_production_db_substitution_attempt():
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token-db"}
    
    # 5. production database substitution attempt
    payload = {"input": json.dumps({"db_path": "new_prod.db", "dry_run": False})}
    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "failure"
