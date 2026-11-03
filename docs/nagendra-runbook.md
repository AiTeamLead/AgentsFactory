# AgentsFactory Developer Runbook

This runbook provides daily operational commands and troubleshooting steps for AgentsFactory.

## 1. Start the Project (Dashboard)
To start the Command Center dashboard:
```bash
uv run streamlit run src/agentkit/observability/command_center.py
```
*(Available at http://localhost:8501)*

## 2. Run Agents Manually
You can run any agent directly via Python:
```bash
# Post to LinkedIn
python src/agents/linkedin_poster.py

# Load leads
python src/agents/lead_loader.py --download

# Sync Notion
python src/agents/sync_leads_notion.py
```

## 3. Run Tests
The test suite covers the `agentkit` core:
```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_circuit_breaker.py
```

## 4. Automation & Crons
Check installed cron jobs:
```bash
crontab -l
```

Install/Reinstall cron jobs:
```bash
bash setup/install-crons.sh
```

## 5. Check Database
Open the SQLite metrics database:
```bash
sqlite3 agentsfactory_metrics.db
```
Useful queries:
```sql
SELECT count(*) FROM leads;
SELECT * FROM agent_activity ORDER BY created_at DESC LIMIT 10;
```

## 6. Docker Operations
Run the environment using Docker Compose:
```bash
# Build and start
docker-compose up --build -d

# Check logs
docker-compose logs -f dashboard
```

## 7. Troubleshooting
*   **Missing API Keys:** Ensure `.env` is populated with `NOTION_API_KEY` and `OCOYA_API_KEY`.
*   **Dependency Errors:** Run `uv sync` or `uv pip install -r requirements.txt` (or via pyproject.toml).
*   **Docker Dashboard Fails:** The `docker-compose.yml` might reference `dashboard.py`. Update it to `command_center.py`.

## 8. Git Operations
Always work on your branch:
```bash
git checkout -b nagendra-feature-name
git commit -m "Description of changes"
git push origin nagendra-feature-name
```
