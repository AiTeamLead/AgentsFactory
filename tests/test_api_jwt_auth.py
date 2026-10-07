import pytest
import os
import jwt
import time
from fastapi.testclient import TestClient
from agentkit.api.app import app
from agentkit.api.security import JWTAuthProvider

# Helper to generate JWT
def generate_jwt(secret="secret", payload=None, headers=None):
    return jwt.encode(payload or {}, secret, algorithm="HS256", headers=headers)

@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    monkeypatch.setenv("AUTH_PROVIDER", "jwt")
    monkeypatch.setenv("JWT_SECRET", "supersecret")
    monkeypatch.setenv("JWT_ISSUER", "test_issuer")
    monkeypatch.setenv("JWT_AUDIENCE", "test_audience")
    monkeypatch.setenv("JWT_ALGORITHMS", "HS256")
    
    import agentkit.api.security as security
    old_provider = security.auth_provider
    security.auth_provider = security.JWTAuthProvider()
    yield
    security.auth_provider = old_provider

def test_jwt_missing_header():
    client = TestClient(app)
    response = client.post("/agents/content_writer/run", json={"input": "{}"})
    assert response.status_code == 401

def test_jwt_invalid_signature():
    client = TestClient(app)
    token = generate_jwt(secret="wrongsecret", payload={"sub": "user1"})
    response = client.post("/agents/content_writer/run", json={"input": "{}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Invalid signature" in response.text or "signature" in response.text.lower()

def test_jwt_expired():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "exp": time.time() - 10})
    response = client.post("/agents/content_writer/run", json={"input": "{}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.text.lower()

def test_jwt_wrong_issuer():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "wrong_issuer", "aud": "test_audience"})
    response = client.post("/agents/content_writer/run", json={"input": "{}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "issuer" in response.text.lower()

def test_jwt_wrong_audience():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "test_issuer", "aud": "wrong_audience"})
    response = client.post("/agents/content_writer/run", json={"input": "{}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "audience" in response.text.lower()

def test_jwt_valid_but_no_permission():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "test_issuer", "aud": "test_audience", "scope": ""})
    response = client.post("/agents/lead_loader/run", json={"input": "{}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_jwt_valid_with_safe_permission():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "test_issuer", "aud": "test_audience", "scope": "agent:execute_safe"})
    response = client.post("/agents/content_writer/run", json={"input": '{"dry_run": true}'}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_jwt_valid_with_social_permission():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "test_issuer", "aud": "test_audience", "scope": "social_media_write agent:execute_safe"})
    # dry_run = True for safety
    payload = '{"action": "generate", "dry_run": true}'
    response = client.post("/agents/content_scheduler/run", json={"input": payload}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_jwt_content_scheduler_dangerous_blocked():
    client = TestClient(app)
    token = generate_jwt(secret="supersecret", payload={"sub": "user1", "iss": "test_issuer", "aud": "test_audience", "scope": "agent:execute_safe"})
    # dry_run = False
    payload = '{"action": "generate", "dry_run": false}'
    response = client.post("/agents/content_scheduler/run", json={"input": payload}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
