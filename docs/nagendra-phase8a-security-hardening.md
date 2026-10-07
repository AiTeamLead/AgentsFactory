# Phase 8A: Execution Security Hardening

## 1. Identified Vulnerability
During the Phase 7 review, a path traversal and arbitrary database substitution vulnerability was identified in the `lead_loader` agent's public API contract. 
Specifically, the `test_db_path` parameter was exposed via the JSON execution payload. An authenticated caller with `database_write` permissions could bypass intended directory constraints by passing `"test_db_path": "../../sensitive.db"`. 
Since SQLite natively handles file creation on connect, this allowed attackers to truncate or create arbitrary databases on the host filesystem.

## 2. Root Cause
The `run_lead_loader` script accepted `test_db_path` as an explicit function argument, which `StandaloneAgentAdapter` dynamically mapped from the incoming JSON `**kwargs`. The connection orchestrator (`get_db`) then blindly mounted the user-provided string.

## 3. Mitigation
The `test_db_path` parameter has been **completely removed** from the public execution function signature in `lead_loader.py`. 
The production database path is now strictly determined by server-side configurations. Specifically:
*   The API payload no longer accepts arbitrary paths.
*   The `get_db()` and `init_db()` functions were refactored to read from a server-side environment variable (`LEAD_LOADER_DB_PATH`) falling back to the immutable `DB_PATH` constant.
*   Attempting to pass `test_db_path` or `db_path` in the JSON payload now triggers a Python `TypeError` inside the Adapter thread due to unexpected keyword arguments, resulting in a safe `500 Internal Server Error` that completely halts execution before SQLite connection.

## 4. Database Boundary
The database connection is no longer dictated by the client context. Tests utilizing the API now natively overwrite the localized `os.environ["LEAD_LOADER_DB_PATH"]` during the test runner loop, perfectly imitating production deployments without leaking test pathways into the REST surface.

## 5. Filesystem Boundary
Removing the client's ability to dictate paths hardens the filesystem. `lead_loader` can no longer be weaponized to overwrite system configurations, `/etc/` directories, or parallel tenant databases.

## 6. Permission Boundary
The strict segregation of `agent:execute_safe`, `database_write`, and `social_media_write` was re-verified. 
*   An `agent:execute_safe` token cannot trigger live writes regardless of payload manipulation.
*   A `database_write` token is now explicitly constrained to the server's configured SQLite path.

## 7. Dry-Run Behavior
The `dry_run` safety mechanism was validated. Passing `dry_run: True` shortcuts execution before SQLite table locking and before Ocoya POST requests. 

## 8. Test Results
Comprehensive testing was added via `test_api_database_security.py`.
1.  **Valid Path**: Tested successfully using environmental variable mocking.
2.  **`../` Traversal**: Attempted via JSON payload; blocked and neutralized (`500`).
3.  **Absolute Path Escape**: Attempted via JSON payload; blocked and neutralized (`500`).
4.  **Substitution Attempt**: Blocked and neutralized (`500`).

## 9. Remaining Risks
*   Environment Variable Spillage: If a production server is compromised to the point of allowing arbitrary ENV manipulation, the database path can still be hijacked (though this requires underlying host compromise, not an API vulnerability).
*   CSV Input Traversal: Future features allowing CSV uploads must rigidly enforce path sanitization to prevent similar traversal tactics on the `download_csv` methods.

## 10. Production Requirements
This addresses the immediate critical host vulnerability. However, the system is not yet Production Ready. Moving to Production still strictly requires replacing the `MOCK_API_KEYS` dictionary with a rigorous JWT/OIDC evaluation layer.
