# Lead Loader API Integration

## 1. Architecture
The `lead_loader.py` agent is the second agent seamlessly integrated into the AgentKit FastAPI architecture. It utilizes the established Phase 4 pattern:
`FastAPI Route → AgentRegistry → AgentContract → StandaloneAgentAdapter → lead_loader.run_lead_loader() → SQLite → Observability`.

## 2. Agent Contract
*   **agent_id**: `lead_loader`
*   **capabilities**: `lead_management`, `database_write`, `csv_import`
*   **execution_mode**: `sync`
*   **required_permissions**: `db_write`

## 3. Registry Registration
The agent is registered dynamically during startup via `src/agentkit/agents/lead_loader_registration.py`. This maps the JSON execution API to the underlying functional Python implementation.

## 4. Adapter Usage
We rely heavily on `StandaloneAgentAdapter`. It translates the API stringified JSON `PipelineState` into dictionary arguments and executes `run_lead_loader(download=True, dry_run=False, test_db_path=None)` natively.

## 5. Input Schema
*   `download` (boolean, default: True): Determines whether fresh leads are pulled from Google Sheets.
*   `dry_run` (boolean, default: False): Safe mode that bypasses database modification entirely.
*   `test_db_path` (string, default: ""): Safe mode specifying a temporary SQLite path for data validation instead of modifying the global `agentsfactory_metrics.db`.

## 6. Output Schema
Returns database insertion metrics upon success:
*   `total_inserted`: int
*   `errors`: int
*   `hot_leads`: int
*   `great_leads`: int

## 7. Database Behavior
If executed without `dry_run` or `test_db_path`, the agent exhibits DESTRUCTIVE behavior. It drops the `leads` table and recreates it before performing a massive batch insert of downloaded CSV data. This behavior strictly mirrors the legacy CLI behavior. 

## 8. Safe Execution
To prevent dropping production leads during API evaluations or routine pings, the `run_lead_loader` wrapper introduces two safe testing paths:
1.  **Dry Run**: Returning a simulated success without running any I/O or DB transactions.
2.  **Isolated DB Mode**: Executing the full download and insertion lifecycle against a dynamically passed `test_db_path`.

## 9. Observability
API calls inherently generate an `AgentResult` object. This seamlessly injects execution duration, errors, success statuses, and token counts natively into the overarching `agentkit` context and Command Center observability.

## 10. CLI Usage
The standard invocation `python src/agents/lead_loader.py --download` or `--stats` is fully unaffected.

## 11. Cron Usage
Existing crontab jobs calling `python src/agents/lead_loader.py --download` function flawlessly because the `__main__` entrypoint was isolated and preserved.

## 12. Testing
`tests/test_lead_loader_api.py` establishes strict functional validations testing both `dry_run` and test database environments. Testing confirms that database schema consistency is maintained perfectly (specifically targeting `social_lead_score` existence) across both the API logic and standard SQLite calls.

## 13. Known Limitations
*   The data synchronization remains fully destructive. There is no upsert logic in `lead_loader.py`; every execution truncates and replaces the `leads` table. Fixing this business logic goes beyond the scope of FastAPI orchestration.
