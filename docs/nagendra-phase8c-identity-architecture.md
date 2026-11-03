# Phase 8C: Production Identity Architecture

## 1. Current Authentication Architecture
Prior to Phase 8C, `JWTAuthProvider` validated symmetric (`HS256`) signatures using a static `JWT_SECRET`. While functionally secure and rigorously isolated from the core codebase, symmetric keys prevent horizontal scaling across trusted third-party providers. Production ecosystems require asymmetric evaluation where the Resource Server (our FastAPI application) verifies tokens minted by an external Identity Provider (Auth0/Okta) without ever possessing the minting secret.

## 2. OIDC Architecture
The Phase 8C implementation successfully introduces an `OIDCAuthProvider` abstracting the PyJWT `PyJWKClient` flow.
**Flow:**
`OIDC Provider (Auth0/Okta)` -> `Mints RS256 JWT` -> `Client REST Call` -> `OIDCAuthProvider` -> `Fetches JWKS` -> `Cryptographically Verifies Signature` -> `Normalizes into User Identity` -> `RBAC` -> `Execution`.

## 3. JWT Validation & JWKS
*   **JWKS Client**: `OIDCAuthProvider` initiates a cached `PyJWKClient(OIDC_JWKS_URI)`.
*   **Validation**: It inspects the incoming JWT unverified header for the Key ID (`kid`), securely retrieves the matching RSA public key from the OIDC provider's `.well-known/jwks.json`, and natively evaluates the token's structural cryptography.
*   It inherently enforces Signature validity, Token Expiration (`exp`), Audience (`aud`), and Issuer (`iss`).

## 4. Key Rotation
The implementation inherently supports native key rotation. `PyJWKClient` caches signing keys inside the FastAPI worker memory. If the Identity Provider rotates their signing key, the newly minted JWT will present an unrecognized `kid`. PyJWT natively purges its cache and initiates a fresh background retrieval to the JWKS URI, preventing application restarts or deployment downtime during rotation schedules.

## 5. Identity Normalization
The `validate_token` method securely normalizes the arbitrary JWT claims into the deterministic `User` Pydantic model:
*   Extracts `sub` as `user_id`. Raises `401` if missing.
*   Parses the `scope` or `scopes` claims safely whether presented as a space-delimited string or a structured array.
*   Appends `auth_method="oidc"`.
This guarantees downstream dependencies (`authorize_agent_execution`) remain blissfully unaware of OIDC or JWT architectures.

## 6. RBAC Integration
Authorization continues to operate exactly as established in Phase 7. Because `OIDCAuthProvider` successfully resolves tokens into identical `User(scopes=[...])` objects, the RBAC engine correctly parses `agent:execute_safe`, `database_write`, and `social_media_write` rules natively.

## 7. Test Authentication
`TestAuthProvider` (mock dictionary) and `JWTAuthProvider` (symmetric `HS256`) remain isolated entities. If `settings.is_production` evaluates true, the application natively locks `TestAuthProvider` with a fatal `ValueError`.

## 8. Production Configuration
The deployment configuration is exclusively environment-driven:
*   `AUTH_PROVIDER=oidc`
*   `OIDC_ISSUER=https://<tenant>.auth0.com/`
*   `OIDC_AUDIENCE=https://api.agentsfactory.com`
*   `OIDC_JWKS_URI=https://<tenant>.auth0.com/.well-known/jwks.json`
*   `OIDC_ALLOWED_ALGORITHMS=RS256`

## 9. Security Controls
*   Unsigned tokens or unknown algorithms inherently trigger `Malformed Token` or `Invalid signature` `401` crashes.
*   Spoofed JWKS configurations are mitigated by server-side definition (`OIDC_JWKS_URI` cannot be supplied via API header payload).
*   Bearer tokens are never logged or echoed inside `AgentResult` schemas.

## 10. CLI/CRON Boundary
Unchanged. The Local execution methods bypass the HTTP pipeline exactly as expected.

## 11. Failure Handling
*   JWKS Network Timeouts or resolution errors bubble explicitly as `JWKS error` `401` blockades, preventing fail-open authorization.
*   Malformed header structures (missing `kid`) trigger `401`.

## 12. Risks
*   **SSRF (Server-Side Request Forgery)**: Because `PyJWKClient` initiates an outbound HTTPS call, configuring `OIDC_JWKS_URI` maliciously could induce server requests to internal IP address spaces. Production infrastructure must restrict outbound egress configurations.
*   **Rate Limiting**: Without a WAF/Gateway layer, unauthenticated users could spam invalid JWTs, forcing computational decoding loads onto the Python worker threads.

## 13. Production Deployment Requirements
1.  **Production Identity Provider**: Instantiating a live tenant (Auth0/Okta/Microsoft Entra ID) to mint these tokens.
2.  **API Gateway**: Implementing AWS API Gateway / Kong to throttle requests upstream.
3.  **HTTPS Termination**: Guaranteeing TLS traffic between clients and the orchestrator.

## 14. Production Readiness
**Production Ready**. 
The Python execution core is fully compliant with scalable, key-rotated enterprise identity architectures. It is architecturally decoupled, mathematically sound, and rigorously tested against invalid parameters. Moving to true external environments now strictly depends on infrastructure (Gateway/OIDC tenant creation) rather than Python execution code.
