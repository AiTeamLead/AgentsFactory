import re

with open("src/agentkit/api/security.py", "r") as f:
    content = f.read()

oidc_class = """
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
        except Exception as e:
            # Catch all structural malformations safely
            raise HTTPException(status_code=401, detail="Malformed token")

"""

# Insert the class right before TestAuthProvider
content = content.replace("class TestAuthProvider(AuthenticationProvider):", oidc_class + "class TestAuthProvider(AuthenticationProvider):")

# Update get_auth_provider
auth_factory = """def get_auth_provider() -> AuthenticationProvider:
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
"""

# Replace old factory
import re
content = re.sub(r'def get_auth_provider\(\) -> AuthenticationProvider:.*?# Initialize globally for FastAPI', auth_factory + '\n# Initialize globally for FastAPI', content, flags=re.DOTALL)

with open("src/agentkit/api/security.py", "w") as f:
    f.write(content)
