import os
import jwt
from typing import List, Optional
from abc import ABC, abstractmethod
from fastapi import Header, HTTPException
from pydantic import BaseModel
from agentkit.config import settings

class User(BaseModel):
    username: str
    scopes: List[str]
    issuer: str = ""
    auth_method: str = "mock"

class AuthenticationProvider(ABC):
    @abstractmethod
    def validate_token(self, token: str) -> User:
        pass

class JWTAuthProvider(AuthenticationProvider):
    def __init__(self):
        self.secret = os.environ.get("JWT_SECRET", "")
        self.audience = os.environ.get("JWT_AUDIENCE", None)
        self.issuer = os.environ.get("JWT_ISSUER", None)
        self.algorithms = [alg.strip() for alg in os.environ.get("JWT_ALGORITHMS", "HS256,RS256").split(",")]

    def validate_token(self, token: str) -> User:
        if not self.secret:
            raise HTTPException(status_code=500, detail="JWT_SECRET is not configured for production environment")
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer
            )
            
            user_id = payload.get("sub", "")
            scope_claim = payload.get("scope", payload.get("scopes", []))
            if isinstance(scope_claim, str):
                scopes = scope_claim.split()
            elif isinstance(scope_claim, list):
                scopes = scope_claim
            else:
                scopes = []
                
            return User(
                username=user_id,
                scopes=scopes,
                issuer=payload.get("iss", ""),
                auth_method="jwt"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidIssuerError:
            raise HTTPException(status_code=401, detail="Invalid issuer")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Invalid audience")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Invalid signature")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


from jwt import PyJWKClient

class OIDCAuthProvider(AuthenticationProvider):
    def __init__(self):
        self.jwks_uri = os.environ.get("OIDC_JWKS_URI")
        self.audience = os.environ.get("OIDC_AUDIENCE")
        self.issuer = os.environ.get("OIDC_ISSUER")
        self.algorithms = [alg.strip() for alg in os.environ.get("OIDC_ALLOWED_ALGORITHMS", "RS256").split(",")]
        
        if not self.jwks_uri:
            raise ValueError("OIDC_JWKS_URI must be configured for OIDC authentication")
            
        self.jwks_client = PyJWKClient(self.jwks_uri, cache_keys=True)

    def validate_token(self, token: str) -> User:
        try:
            # Extract the unverified header to get the key ID (kid)
            # and verify the signing key through the cached JWKS client
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer
            )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Missing subject claim (sub)")
                
            scope_claim = payload.get("scope", payload.get("scopes", []))
            if isinstance(scope_claim, str):
                scopes = scope_claim.split()
            elif isinstance(scope_claim, list):
                scopes = scope_claim
            else:
                scopes = []
                
            return User(
                username=user_id,
                scopes=scopes,
                issuer=payload.get("iss", ""),
                auth_method="oidc"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidIssuerError:
            raise HTTPException(status_code=401, detail="Invalid issuer")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Invalid audience")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Invalid signature")
        except jwt.PyJWKClientError as e:
            raise HTTPException(status_code=401, detail=f"JWKS error: {str(e)}")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            # Catch all structural malformations safely
            raise HTTPException(status_code=401, detail="Malformed token")

class TestAuthProvider(AuthenticationProvider):
    def __init__(self):
        if settings.is_production:
            raise ValueError("TestAuthProvider cannot be used in production!")
            
        self.mock_keys = {
            "test-token-admin": User(username="admin", scopes=["*"], auth_method="test"),
            "test-token-safe": User(username="safe_user", scopes=["agent:execute_safe"], auth_method="test"),
            "test-token-social": User(username="social_user", scopes=["agent:execute_safe", "social_media_write"], auth_method="test"),
            "test-token-db": User(username="db_user", scopes=["agent:execute_safe", "database_write"], auth_method="test")
        }

    def validate_token(self, token: str) -> User:
        user = self.mock_keys.get(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return user

def get_auth_provider() -> AuthenticationProvider:
    provider_type = os.environ.get("AUTH_PROVIDER", "test").lower()
    
    if provider_type == "test":
        if settings.is_production:
            raise ValueError("Test authentication provider is forbidden in production environment.")
        return TestAuthProvider()
    elif provider_type == "jwt":
        return JWTAuthProvider()
    elif provider_type == "oidc":
        return OIDCAuthProvider()
    else:
        raise ValueError(f"Unknown auth provider: {provider_type}")

# Initialize globally for FastAPI
try:
    auth_provider = get_auth_provider()
except ValueError as e:
    import logging
    logging.getLogger(__name__).warning(f"Auth provider initialization failed: {e}")
    auth_provider = None

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Authentication dependency: Validates token and establishes identity."""
    if not auth_provider:
        raise HTTPException(status_code=500, detail="Authentication provider is not properly configured")
        
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.lower().startswith("bearer "):
        # For backward compatibility with the mock keys that might not pass 'Bearer '
        token = authorization.strip()
    else:
        # standard bearer format
        token = authorization[7:].strip()
        
    return auth_provider.validate_token(token)

import json
def authorize_agent_execution(contract, request_body: str, user: User) -> None:
    """Authorization logic: Verifies user scopes against AgentContract requirements."""
    # If admin, permit all
    if "*" in user.scopes:
        return

    is_safe_run = False
    try:
        if request_body:
            payload = json.loads(request_body)
            is_safe_run = bool(payload.get("dry_run", False))
    except json.JSONDecodeError:
        pass

    required = contract.safe_permissions if is_safe_run else contract.required_permissions

    for req in required:
        if req not in user.scopes:
            raise HTTPException(
                status_code=403, 
                detail=f"Unauthorized: Missing required permission '{req}' for this execution."
            )
