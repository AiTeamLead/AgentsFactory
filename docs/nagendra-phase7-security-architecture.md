# Phase 7: Security Architecture

## 1. Current Security Problem
Prior to Phase 7, the Agent Execution API (`POST /agents/{agent_id}/run`) operated entirely unauthenticated. While local execution models were isolated, the integration of `lead_loader` (database truncation) and `content_scheduler` (social media publishing via Ocoya) introduced significant risks. Any unauthenticated caller could execute dangerous functions leading to potential data loss or unauthorized production operations.

## 2. Authentication Model
We introduced a minimal authentication model targeting the local development and internal-tooling stages. A dependency injection mechanism (`get_current_user`) reads the HTTP `Authorization` header.
*   Header format: `Bearer {token}`
*   If omitted, the API correctly responds with `401 Unauthorized`.
*   A static mapping of token scopes defines mock user sessions for test validations (`test-token-admin`, `test-token-safe`, `test-token-social`, `test-token-db`).

## 3. Authorization Model
Authentication verifies identity, but authorization verifies intent. Before bridging the HTTP payload to the `StandaloneAgentAdapter`, the `run_agent` API resolves the `AgentContract`. The system cross-references the requested action context with the user's encoded scopes.
If the scopes do not meet the minimums, `403 Forbidden` is returned, preventing the Adapter from launching the underlying script.

## 4. Permission Model
Permissions are modeled as capability strings. 
*   `agent:execute_safe`: Grants access to purely generative LLM endpoints or explicitly safe sandboxed dry-runs.
*   `social_media_write`: Grants write access to Ocoya publishing routines.
*   `database_write`: Grants truncation and CSV loading powers.
*   `*`: Admin override.

## 5. Agent Risk Classification
Agents declare their risk metadata inside `AgentContract`.
*   **content_writer_pilot**: `LOW` risk. Relies entirely on LLM APIs. Requires `agent:execute_safe`.
*   **lead_loader**: `MEDIUM` risk. Modifies backend SQLite tables. Requires `database_write`. Safe dry-run requires `agent:execute_safe`.
*   **content_scheduler**: `HIGH` risk. Dispatches actual LinkedIn posts to production. Requires `social_media_write`. Safe dry-run requires `agent:execute_safe`.

## 6. Execution Flow
1. HTTP `POST /agents/content_scheduler/run` (Header: `Authorization: Bearer X`)
2. FastAPI `Depends(get_current_user)` -> extracts `X` -> generates `User`.
3. Route looks up `content_scheduler` contract.
4. Payload parsed; `authorize_agent_execution` matches user scopes with `contract.required_permissions`.
5. Authorized payload reaches `StandaloneAgentAdapter`.
6. Agent function executes natively.

## 7. Dangerous Agent Protection
`content_scheduler` acts as our primary test case. The `authorize_agent_execution` routine actively peeks at the execution JSON to identify `dry_run: True`. If `dry_run` is absent or false, the strict `required_permissions` guard applies. The API successfully rejects social-media writes from unauthorized tokens without executing the Ocoya backend.

## 8. Audit / Observability
The injection of authentication scopes allows future AgentKit traces to record the `User` invoking the pipeline. API keys are strictly evaluated in memory and discarded. AgentResults format cleanly without dumping credentials into stdout.

## 9. CLI/CRON Security Boundary
This architecture isolates HTTP protections strictly to the FastAPI wrapper. Native commands (`python src/agents/content_scheduler.py --generate`) and internal crontabs explicitly bypass the REST middleware, preventing legacy scheduling breaks. This intentional separation of concerns secures external traffic without sabotaging internal operating system workloads.

## 10. Future JWT/OIDC Integration
The current `MOCK_API_KEYS` dictionary mapping should be replaced by a JWT validation library (e.g., `PyJWT`). The `get_current_user` method can extract an RS256 signature from Azure/Auth0/Okta, verifying audience and issuer before decoding the string list of `.scopes`.

## 11. Future Enterprise IAM Integration
For deep multi-tenant integration (Phase 10/11), `User` mappings will point directly to a Postgres relational model handling Role-Based Access Control (RBAC), resolving organizational boundaries to grant access only to specific tenants' databases.

## 12. Known Limitations
*   Mock mapping is static. Moving beyond staging requires live credential rotation.
*   CLI processes remain unauthenticated. If internal terminal access is compromised, the APIs can be bypassed.
