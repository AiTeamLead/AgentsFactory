# Phase 9: Agent Catalog Expansion

## 1. Agent Catalog
The AgentKit execution architecture currently encompasses the following registered standalone agents:

| Agent ID | Capabilities | Risk Level |
| :--- | :--- | :--- |
| `lead_loader` | `data_processing`, `crm` | HIGH |
| `content_scheduler` | `scheduling`, `social_media` | HIGH |
| `content_writer` | `content_generation`, `copywriting` | MEDIUM |
| `daily_briefing` | `reporting`, `analytics` | LOW |

## 2. Newly Migrated Agents (Phase 9A)

### 2.1 Content Writer (`content_writer`)
*   **Description**: Generates infotainment-style content across pillars and platforms. Originally prototyped via `content_writer_pilot`, now fully migrated using the active execution implementation.
*   **Input Schema**:
    ```json
    {
      "pillar": "string",
      "platform": "string",
      "topic": "string",
      "count": "integer",
      "dry_run": "boolean"
    }
    ```
*   **Output Schema**:
    ```json
    {
      "result": [{"title": "string", "content": "string"}]
    }
    ```
*   **Permissions**: `database_write` (Dangerous), `agent:execute_safe` (Dry Run).
*   **Security Controls**: Directly writes to `content_calendar` and `agent_activity`. Execution with `dry_run=False` mandates `database_write` privileges. Safe fallback is achieved utilizing `dry_run=True`. Arbitrary file writes and SQL injection risks are nullified.
*   **CLI/Cron**: Natively backwards compatible. Execution via `python src/agents/content_writer.py` persists uninterrupted.

### 2.2 Daily Briefing (`daily_briefing`)
*   **Description**: Aggregates the `agentsfactory_metrics.db` and generates a morning briefing inclusive of automation health, content drafted, and leads sourced.
*   **Input Schema**: `{}` (Empty)
*   **Output Schema**:
    ```json
    {
      "result": "string"
    }
    ```
*   **Permissions**: `agent:execute_safe`
*   **Security Controls**: Read-only extraction across metric tables. Logs execution completion minimally. Execution relies natively on standard `agent:execute_safe` privileges. No arbitrary queries allowed.
*   **CLI/Cron**: Scripts correctly wrap `generate_briefing()`. Unaltered structure ensures local cron execution at 8:00 AM IST remains intact.

## 3. Migration Status
**Migrated**:
*   `lead_loader`
*   `content_scheduler`
*   `content_writer` (Upgraded from pilot)
*   `daily_briefing`

**Remaining Agents (Candidates for Phase 9B)**:
*   `lead_finder`
*   `linkedin_poster`
*   `outreach_agent`
*   `weekly_review`

## 4. Test Coverage
*   **Old Count**: 115
*   **New Count**: 117
*   **Added**:
    *   `test_api_content_writer_execution_dangerous`: Validates RBAC correctly blocks live DB writes without `database_write`.
    *   `test_api_daily_briefing_discovery` & `test_api_daily_briefing_execution`: Checks read-only registry insertion and valid execution.

## 5. Recommended Next Migration Order
1.  **`weekly_review`**: Extends the reporting capabilities demonstrated by `daily_briefing`.
2.  **`lead_finder`**: Integrates data scraping inputs and coordinates directly with `lead_loader`.
3.  **`linkedin_poster`**: Introduces heavy social-media side effects (Ocoya). Requires precise dry-run protection mappings.
