# Content Scheduler API Integration

## 1. Architecture
The `content_scheduler.py` agent is the third agent integrated into the AgentKit FastAPI architecture. It utilizes the proven execution pattern:
`FastAPI Route → AgentRegistry → AgentContract → StandaloneAgentAdapter → content_scheduler.run_content_scheduler() → Ocoya API → Observability`.

## 2. Agent Contract
*   **agent_id**: `content_scheduler`
*   **capabilities**: `social_media_scheduling`, `content_generation`, `api_integration`
*   **execution_mode**: `sync`
*   **required_permissions**: `social_media_write`

## 3. Registry Registration
The agent is dynamically registered during startup via `src/agentkit/agents/content_scheduler_registration.py`.

## 4. Adapter Usage
The generic `StandaloneAgentAdapter` bridges the HTTP stringified payload dictionary `**kwargs` into the execution of `run_content_scheduler(action, pillar, posts_per_day, dry_run)`.

## 5. Input Schema
*   `action` (string, enum: ["generate", "calendar", "schedule_week"], default: "generate")
*   `pillar` (string, optional): Specific content pillar topic for generation.
*   `posts_per_day` (integer, default: 1): Number of daily posts to queue during `schedule_week`.
*   `dry_run` (boolean, default: False): Critical parameter enabling safe bypass of external API calls to Ocoya.

## 6. Output Schema
Returns structured dictionaries mapped identically to the original function:
*   `action`: string
*   `post` / `calendar` / `scheduled`: mixed outputs depending on the `action` invoked.
*   `posts`: Array of simulated or live scheduled posts
*   `dry_run`: boolean

## 7. Safety Mechanisms
If executed without `dry_run=True`, the agent makes real, authenticated `HTTP POST` writes to the `Ocoya API` for LinkedIn publishing. To safely permit continuous integration testing and UI mockup logic, `dry_run` overrides the `schedule_linkedin_post()` wrapper internally while yielding simulated return structures identical to live data.

## 8. Observability
API calls natively wrap into the generic `AgentResult` object (returning `latency_ms` and generic execution successes), directly inherited by the unified `agentkit` observability engine.

## 9. Backward Compatibility
The underlying script preserves its CLI entry points unaltered:
*   `--generate`
*   `--schedule-week`
*   `--calendar`
Cron executions natively bound to these parameters will execute synchronously as designed without noticing the API augmentation.

## 10. Testing
Comprehensive validation logic is located in `tests/test_content_scheduler_api.py`. Testing confirms that no live external POST requests are dispatched during `dry_run` modes.

## 11. Known Limitations
*   `--calendar` currently outputs a type error if `ocoya_client.py` fails to fetch active data without an API key (returning a generic string instead of a dictionary). This logic was explicitly omitted from fixing to preserve raw business logic boundaries inside `content_scheduler.py`.
