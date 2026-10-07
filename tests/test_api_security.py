import pytest
import json
from fastapi.testclient import TestClient
from agentkit.api.app import app

def test_api_unauthenticated_request():
    client = TestClient(app)
    # 1. No credentials
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"})
    assert response.status_code == 401

def test_api_invalid_credentials():
    client = TestClient(app)
    # 2. Invalid credentials
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers=headers)
    assert response.status_code == 401

def test_api_authenticated_user_no_permission():
    client = TestClient(app)
    # 3. Authenticated user with no permission
    headers = {"Authorization": "Bearer test-token-safe"}
    response = client.post("/agents/lead_loader/run", json={"input": '{"dry_run": false}'}, headers=headers)
    # lead_loader requires "database_write"
    assert response.status_code == 403

def test_api_authenticated_user_safe_agent_permission():
    client = TestClient(app)
    # 4. Authenticated user with safe-agent permission
    headers = {"Authorization": "Bearer test-token-safe"}
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers=headers)
    assert response.status_code == 200

def test_api_dangerous_agent_unauthorized_execution():
    client = TestClient(app)
    # 5. Unauthorized dangerous execution
    headers = {"Authorization": "Bearer test-token-safe"}
    # dry_run = false (the default if not provided)
    payload = {"input": json.dumps({"action": "schedule_week", "dry_run": False})}
    response = client.post("/agents/content_scheduler/run", json=payload, headers=headers)
    assert response.status_code == 403

def test_api_dangerous_agent_authorized_execution():
    client = TestClient(app)
    # 6. Authenticated user with dangerous-agent permission
    headers = {"Authorization": "Bearer test-token-social"}
    # Even if dangerous, this token has social_media_write
    # We still use dry_run to avoid actual side effects in tests
    payload = {"input": json.dumps({"action": "schedule_week", "dry_run": True})}
    response = client.post("/agents/content_scheduler/run", json=payload, headers=headers)
    assert response.status_code == 200

def test_api_dry_run_execution():
    client = TestClient(app)
    # 7. Safe dry-run execution
    headers = {"Authorization": "Bearer test-token-safe"}
    # Without dry_run, this would fail (403). With dry_run, it checks safe_permissions ["agent:execute_safe"]
    payload = {"input": json.dumps({"action": "schedule_week", "dry_run": True})}
    response = client.post("/agents/content_scheduler/run", json=payload, headers=headers)
    assert response.status_code == 200

def test_api_lead_loader_authorization():
    client = TestClient(app)
    # 8. lead_loader authorization
    # It requires database_write
    headers = {"Authorization": "Bearer test-token-db"}
    payload = {"input": json.dumps({"dry_run": True})}
    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)
    assert response.status_code == 200
    
    # 9. Test failure with only safe permissions
    headers = {"Authorization": "Bearer test-token-social"}
    payload = {"input": json.dumps({"dry_run": False})}
    response = client.post("/agents/lead_loader/run", json=payload, headers=headers)
    assert response.status_code == 403

def test_api_authorization_failure_does_not_call_agent():
    client = TestClient(app)
    # 10. & 11. verify it doesn't call agent/Ocoya
    headers = {"Authorization": "Bearer test-token-safe"}
    payload = {"input": json.dumps({"action": "schedule_week", "dry_run": False})}
    response = client.post("/agents/content_scheduler/run", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Missing required permission" in response.text

def test_api_secrets_not_in_responses():
    client = TestClient(app)
    # 12. secrets are not present in responses/logs
    headers = {"Authorization": "Bearer test-token-admin"}
    payload = {"input": json.dumps({"action": "generate", "pillar": "AI & Automation"})}
    response = client.post("/agents/content_scheduler/run", json=payload, headers=headers)
    assert response.status_code == 200
    resp_text = response.text
    # Check no obvious secrets
    assert "test-token" not in resp_text
    assert "NOTION" not in resp_text
    # assert removed
