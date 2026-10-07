# AgentsFactory Project Understanding

## 1. Executive Summary
AgentsFactory is a self-cloning AI automation agency infrastructure. It is designed to run multi-agent AI systems with production-grade rigor. Unlike a simple chatbot or standalone script, it treats multi-agent workflows as distributed systems, featuring state pipelines, circuit breakers, fallback mechanisms, human-in-the-loop (HITL) gates, and context management. It targets businesses seeking robust, automated solutions for social media, lead generation, and content creation, with a vision of becoming an enterprise-grade platform.

## 2. Main Business Idea
AgentsFactory solves the problem of unreliable, single-threaded AI bots by providing a resilient, multi-agent orchestration layer. It automates complex business processes (like LinkedIn posting, engagement, and lead outreach) across multiple platforms while ensuring stability and monitoring through a Command Center dashboard.

### Differences:
*   **Normal Chatbot:** Only responds to prompts; AgentsFactory proactively executes complex workflows.
*   **Single AI Agent:** Prone to hallucinations and failures; AgentsFactory uses circuit breakers and fallbacks.
*   **n8n/Zapier:** Pure logic/triggers; AgentsFactory embeds LLM reasoning and routing.
*   **Simple Python Script:** Lacks observability, state management, and robustness.

## 3. Main Technical Idea
The core architecture is built around a `PipelineState` model that flows through a Topology Engine (Sequential, Parallel, Hierarchical, Evaluator-Optimizer). It ensures reliability using circuit breakers (preventing cascading failures), context managers (handling token budgets), and fallback chains. Agents are integrated via a centralized orchestration system that interfaces with external APIs (Ocoya, Notion, LinkedIn).

## 4. Repository Structure
*   `src/agentkit/`: Core framework (circuit breakers, context, orchestration, models).
*   `src/agents/`: Implementations of specific agents (LinkedIn Poster, Lead Loader, etc.).
*   `src/workflows/`: Complex workflow definitions.
*   `docs/`: Architecture documents, landing pages, research.
*   `setup/`: Shell scripts for bootstrapping, cron installation, and backups.
*   `tests/`: Test suite for framework components.
*   `docker-compose.yml` / `Dockerfile`: Dockerized execution environments.
*   `pyproject.toml` / `uv.lock`: Python dependencies (using Astral's `uv`).
*   `.env.example`: Template for required secrets.

## 5. Architecture
*   **Orchestrator:** Manages execution flow.
*   **Topology Engine:** Implements routing patterns.
*   **Agent Execution:** Uses LLMs and tools under strict `PermissionMatrix`.
*   **Context Management:** Manages tokens and summarization.
*   **Observability:** Streamlit dashboard (`command_center.py`) and traces.

## 6. Agent Architecture
Agents are implemented as Python scripts in `src/agents/`, leveraging the `agentkit` framework.
*   **Implemented:** `linkedin_poster.py`, `content_scheduler.py`, `engagement_agent.py`, `lead_loader.py`
*   **Tools:** Ocoya API, Notion API, SQLite.
*   **Trigger:** Cron jobs.

## 7. Workflow Architecture
Workflows are defined using topology configurations (e.g., `yaml_loader.py` in `agentkit/orchestrator/`). They map out the execution of multiple agents sequentially or in parallel.

## 8. Database/Data Architecture
*   **SQLite:** `agentsfactory_metrics.db` stores leads and agent activity.
*   **Notion:** Synced with the database for human-readable tracking.

## 9. Integration Architecture
*   **Ocoya:** Social media posting.
*   **Notion:** CRM and data syncing.
*   **GitHub:** Automatic backups.
*   **LLMs:** Managed via `agentkit/llm.py` and potentially OpenRouter.

## 10. Dashboard Architecture
*   **Implementation:** Streamlit (`src/agentkit/observability/command_center.py`).
*   **Status:** Live. Connects to SQLite to show Overview, Projects, Revenue, Leads, Content, and Automations.

## 11. Marketplace Architecture
*   **Status:** Display layer exists (HTML docs and GitHub Pages). The backend productization of these workflows into a true SaaS marketplace is largely PLANNED.

## 12. Setup Guide
1.  `git clone https://github.com/phanindraintelligenzit-afk/AgentsFactory.git`
2.  `cd AgentsFactory`
3.  `bash setup/bootstrap.sh`
4.  `cp .env.example .env` and configure keys.
5.  `python src/agents/lead_loader.py --download`
6.  `uv run streamlit run src/agentkit/observability/command_center.py`

## 13. Environment Variables
*   `NOTION_API_KEY`: Required for CRM syncing.
*   `OCoYA_API_KEY`: Required for social media automation.
*   `GITHUB_TOKEN`: Used for backup scripts.

## 14. Command Reference
*   **Start Dashboard:** `uv run streamlit run src/agentkit/observability/command_center.py`
*   **Run Agent:** `python src/agents/linkedin_poster.py`
*   **Install Crons:** `bash setup/install-crons.sh`
*   **Test:** `pytest tests/`

## 15. Testing Guide
Tests cover core framework features (Circuit Breaker, Context, Fallback, etc.) using pytest.
*   Run with: `pytest tests/`

## 16. Docker Guide
The `Dockerfile` builds a Streamlit-based image. `docker-compose.yml` defines an `api` and `dashboard` service.
*   **Note:** The API service points to an undefined run command if the FastAPI app (`src/agentkit/api/app.py`) isn't fully robust, but it mounts volumes and exposes ports.

## 17. Automation/Cron Guide
*   Crons are managed via `setup/install-crons.sh`. They execute specific python scripts in `src/agents/` on a schedule.

## 18. Current Capabilities
*   Social Media Posting (via Ocoya)
*   Lead Loading
*   Dashboard Monitoring
*   Core AgentKit Framework (Circuit breakers, context)

## 19. Partial Capabilities
*   Instagram Posting (Requires media attachment)
*   Full multi-agent workflow orchestration using LangGraph adapter.

## 20. Planned/Roadmap Capabilities
*   Full Marketplace Productization
*   Enterprise Tenant Isolation
*   Advanced RBAC

## 21. Known Issues/Inconsistencies
*   `docker-compose.yml` refers to `src/agentkit/observability/dashboard.py`, but the file is named `command_center.py` in the `Dockerfile`.

## 22. Risks
*   High reliance on Ocoya API.
*   Database concurrency (SQLite in a multi-agent cron environment).

## 23. Recommended Learning Path for a Developer
1.  Read `README.md` and `docs/architecture.md`.
2.  Understand `agentkit/core/circuit_breaker.py` and `models/pipeline.py`.
3.  Review `src/agents/linkedin_poster.py`.

## 24. Glossary
*   **HITL:** Human-In-The-Loop.
*   **Circuit Breaker:** Mechanism to stop cascading failures.
*   **Topology:** The structural pattern of agent execution.

## 25. Final "How AgentsFactory Works" explanation
AgentsFactory operates as a background automation agency. Cron jobs trigger specialized Python agents that pull data (leads, content ideas), process it using LLMs, and execute actions via external APIs (like posting to LinkedIn via Ocoya or syncing data to Notion). All activity is tracked in a local SQLite database, governed by the `agentkit` resilience framework (circuit breakers, fallbacks), and monitored through a Streamlit Command Center dashboard.
