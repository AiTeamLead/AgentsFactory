import pytest
import os
import jwt
import time
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from agentkit.api.app import app

# Generate RS256 key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

unknown_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

def generate_oidc_jwt(private_key_pem, payload=None, headers=None):
    if headers is None:
        headers = {"kid": "test-kid-1"}
    return jwt.encode(payload or {}, private_key_pem, algorithm="RS256", headers=headers)

@pytest.fixture(autouse=True)
def setup_oidc_env(monkeypatch):
    monkeypatch.setenv("AUTH_PROVIDER", "oidc")
    monkeypatch.setenv("OIDC_ISSUER", "https://test.issuer.com")
    monkeypatch.setenv("OIDC_AUDIENCE", "test_audience")
    monkeypatch.setenv("OIDC_JWKS_URI", "https://test.issuer.com/.well-known/jwks.json")
    monkeypatch.setenv("OIDC_ALLOWED_ALGORITHMS", "RS256")
    
    import agentkit.api.security as security
    old_provider = security.auth_provider
    
    # Initialize OIDC provider
    oidc_provider = security.OIDCAuthProvider()
    
    # Mock PyJWKClient.get_signing_key_from_jwt
    # It should return an object that has a 'key' property containing the public key
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    
    def mock_get_signing_key(token):
        # Validate that if they pass a token signed with the unknown key, it will fail 
        # signature validation inside jwt.decode().
        # In reality, get_signing_key_from_jwt checks the 'kid' and returns the key.
        # We will just return our good public key, and if the payload was signed with a bad key, decode fails.
        unverified_headers = jwt.get_unverified_header(token)
        if unverified_headers.get("kid") == "unknown-kid":
            raise jwt.PyJWKClientError("Unable to find a signing key that matches")
        return mock_signing_key
        
    oidc_provider.jwks_client.get_signing_key_from_jwt = MagicMock(side_effect=mock_get_signing_key)
    
    security.auth_provider = oidc_provider
    yield
    security.auth_provider = old_provider

def test_oidc_missing_header():
    client = TestClient(app)
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"})
    assert response.status_code == 401

def test_oidc_valid_rs256():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scope": "agent:execute_safe"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_oidc_invalid_signature():
    client = TestClient(app)
    # Sign with unknown private key, but keep the known kid so our mock returns the valid public key.
    # The signature check will fail because the payload was signed with a different private key.
    token = generate_oidc_jwt(
        unknown_private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scope": "agent:execute_safe"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Invalid signature" in response.text or "signature" in response.text.lower()

def test_oidc_expired():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "exp": time.time() - 10}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.text.lower()

def test_oidc_wrong_issuer():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "wrong_issuer", "aud": "test_audience", "scope": "agent:execute_safe"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "issuer" in response.text.lower()

def test_oidc_wrong_audience():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "wrong_audience", "scope": "agent:execute_safe"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "audience" in response.text.lower()

def test_oidc_unknown_signing_key():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience"},
        headers={"kid": "unknown-kid"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "JWKS error" in response.text or "Malformed token" in response.text

def test_oidc_missing_subject():
    client = TestClient(app)
    # no "sub" claim
    token = generate_oidc_jwt(
        private_key, 
        payload={"iss": "https://test.issuer.com", "aud": "test_audience"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "sub" in response.text.lower() or "subject" in response.text.lower()

def test_oidc_unsupported_algorithm():
    client = TestClient(app)
    # HS256 should be rejected if only RS256 is allowed
    token = jwt.encode(
        {"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience"},
        "some_symmetric_secret",
        algorithm="HS256"
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "signature" in response.text.lower() or "alg" in response.text.lower() or "malformed token" in response.text.lower()

def test_oidc_valid_but_insufficient_permission():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scope": "agent:execute_safe"}
    )
    payload = '{"action": "generate", "dry_run": false}'
    response = client.post("/agents/content_scheduler/run", json={"input": payload}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_oidc_database_write_authorization():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scope": "agent:execute_safe database_write"}
    )
    payload = '{"download": false, "dry_run": false}'
    response = client.post("/agents/lead_loader/run", json={"input": payload}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_oidc_social_media_write_authorization():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scopes": ["agent:execute_safe", "social_media_write"]}
    )
    payload = '{"action": "generate", "dry_run": false}'
    response = client.post("/agents/content_scheduler/run", json={"input": payload}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_oidc_secret_leakage_prevention():
    client = TestClient(app)
    token = generate_oidc_jwt(
        private_key, 
        payload={"sub": "user1", "iss": "https://test.issuer.com", "aud": "test_audience", "scope": "agent:execute_safe"}
    )
    response = client.post("/agents/content_writer/run", json={"input": "{\"dry_run\": true}"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "token" not in response.json().get("output", {}).get("result", {})
    assert "Bearer" not in response.text
