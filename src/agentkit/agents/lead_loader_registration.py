from agentkit.agents.registry import agent_registry
from agentkit.agents.contract import AgentContract
from agentkit.agents.adapter import StandaloneAgentAdapter
from agentkit.models.topology import AgentConfig
from agents.lead_loader import run_lead_loader

def register_lead_loader_agent() -> None:
    """Registers the standalone lead_loader agent into the AgentKit API Registry."""
    contract = AgentContract(
        agent_id="lead_loader",
        name="Lead Loader",
        version="1.0.0",
        description="Downloads leads from Google Sheets and loads them into the local SQLite database.",
        input_schema={
            "download": {"type": "boolean", "default": True, "description": "Whether to download fresh leads"},
            "dry_run": {"type": "boolean", "default": False, "description": "Safe preview mode without DB writes"},
            "test_db_path": {"type": "string", "default": "", "description": "Optional isolated test DB path"}
        },
        output_schema={
            "total_inserted": {"type": "integer"},
            "errors": {"type": "integer"},
            "hot_leads": {"type": "integer"},
            "great_leads": {"type": "integer"}
        },
        capabilities=["lead_management", "database_write", "csv_import"],
        required_tools=[],
        required_permissions=["database_write"],
        safe_permissions=["agent:execute_safe"],
        risk_level="MEDIUM",
        execution_mode="sync"
    )

    def adapter_factory(config: AgentConfig = None, **kwargs) -> StandaloneAgentAdapter:
        if not config:
            config = AgentConfig(agent_id=contract.agent_id, role="data_loader", model="local")
        return StandaloneAgentAdapter(config=config, func=run_lead_loader, **kwargs)

    agent_registry.register(contract, adapter_factory)

# Auto-register on import
register_lead_loader_agent()
