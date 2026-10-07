# Phase 8B: Authentication Architecture

## 1. Current Authentication Problem
Prior to Phase 8B, the execution API relied on `MOCK_API_KEYS`, a static dictionary embedding tokens explicitly into memory. While structurally secure for unit testing by rejecting unauthenticated requests, it inherently prohibited deployment to environments requiring token lifecycle management, signature verification, expiring keys, and integration with dynamic identity providers (Auth0/Okta).

## 2. Authentication Architecture
The system decouples **Authentication** ("Who are you?") from **Authorization** ("What can you do?").
*   **Authentication**: Managed by an `AuthenticationProvider` abstraction injected directly into FastAPI `Depends()`. 
*   **Authorization**: Evaluated dynamically inside the route by comparing the `User` output from the `AuthenticationProvider` against the active `AgentContract` scopes.

## 3. Identity Model
The abstraction yielded an `AuthenticatedIdentity` (mapped as `User` struct):
```python
class User(BaseModel):
    username: str
    scopes: List[str]
    issuer: str = ""
    auth_method: str = "mock" # "jwt", "test"
```
This isolates the execution engine from needing to understand standard JWT claims. It evaluates `scopes` deterministically.

## 4. Token Validation
The `AuthenticationProvider` enforces a strict inheritance pattern, dictating how tokens translate into `User` definitions:
1.  `JWTAuthProvider`: Implements standard `PyJWT` decoding logic.
2.  `TestAuthProvider`: Preserves legacy testing pipelines (`MOCK_API_KEYS`).

## 5. JWT Security
If `AUTH_PROVIDER=jwt`, the system relies entirely on `PyJWT`'s rigorous cryptographic enforcement:
*   **Signature**: Rejected (`InvalidSignatureError`) if the signing key does not match `JWT_SECRET`.
*   **Expiration**: Rejected (`ExpiredSignatureError`) if the payload's `exp` integer lapses.
*   **Audience/Issuer**: Rejected (`InvalidAudienceError` / `InvalidIssuerError`) if the expected `JWT_AUDIENCE` or `JWT_ISSUER` drift.
*   The API never logs bearer tokens or leaks claims in external responses.

## 6. Authorization Integration
The flow proceeds flawlessly:
`HTTP Request` -> `get_current_user()` -> `jwt.decode()` -> `User(scopes)` -> `authorize_agent_execution()` -> `StandaloneAgentAdapter`.
The Authorization engine never handles JSON Web Tokens. It exclusively reads the Python `User` list of scopes.

## 7. Permission Model
The core RBAC layers function perfectly without alteration:
*   `agent:execute_safe`
*   `database_write`
*   `social_media_write`

## 8. Configuration
Environment variables dictate execution environments natively:
*   `AUTH_PROVIDER` (e.g., "jwt", "test")
*   `JWT_SECRET` (Cryptographic key)
*   `JWT_ISSUER` (Identity tenant identifier)
*   `JWT_AUDIENCE` (API Resource target)
*   `JWT_ALGORITHMS` (Defaults to `HS256,RS256`).

## 9. Test Authentication
The `TestAuthProvider` protects local development pipelines without entangling test secrets into production code. A native trap blocks its usage if `settings.is_production` evaluates true, guaranteeing a `ValueError` crash over an insecure boot sequence.

## 10. CLI/CRON Boundary
The CLI and localized Crontabs strictly bypass FastAPI dependencies, executing directly against the Python methods (`python src/agents/content_scheduler.py`). This prevents legacy tasks from requiring convoluted internal M2M token generation schemas.

## 11. Security Controls
*   Invalid tokens (`401`)
*   Missing headers (`401`)
*   Expired/Misaligned tokens (`401`)
*   Lack of valid authorization scope (`403`)
All failures map directly to standard HTTP REST codes without emitting stack traces.

## 12. Future OIDC/SSO Integration
Moving to Okta/Auth0 simply involves refactoring the `JWT_SECRET` resolution into an asynchronous JWKS retrieval routine (mapping the JWKS URI), natively inheriting the rigorous signature tests established.

## 13. Risks
*   **Symmetric Keys**: Currently configured primarily for `HS256` symmetric keys out-of-the-box. Asymmetric `RS256` deployments will require extending the `JWTAuthProvider` to handle public certificate loading.
*   **No Key Rotation Mapping**: Out of scope for this phase.

## 14. Production Readiness
**Staging Ready**. The application is cryptographically safe and structurally compliant with Enterprise IAM design patterns. True Production requires the final integration of the target JWKS endpoints.
