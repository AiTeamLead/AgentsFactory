from agentkit.agents.registry import agent_registry
from agentkit.agents.contract import AgentContract
from agentkit.agents.adapter import StandaloneAgentAdapter
from agentkit.models.topology import AgentConfig
from agents.content_writer import generate_content

def register_content_writer() -> None:
    """Registers the standalone content_writer agent into the AgentKit API Registry."""
    contract = AgentContract(
        agent_id="content_writer",
        name="Content Writer",
        version="1.0.0",
        description="Generates infotainment-style content across pillars and platforms and saves them.",
        input_schema={
            "pillar": {"type": "string"},
            "platform": {"type": "string"},
            "topic": {"type": "string"},
            "count": {"type": "integer"},
            "dry_run": {"type": "boolean", "default": False}
        },
        output_schema={
            "result": {"type": "array", "items": {"type": "object"}}
        },
        capabilities=["content_generation", "copywriting"],
        required_tools=[],
        required_permissions=["database_write"],
        safe_permissions=["agent:execute_safe"],
        risk_level="MEDIUM",
        execution_mode="sync"
    )

    def adapter_factory(config: AgentConfig = None, **kwargs) -> StandaloneAgentAdapter:
        if not config:
            config = AgentConfig(agent_id=contract.agent_id, role="writer", model="local")
        return StandaloneAgentAdapter(config=config, func=generate_content, **kwargs)

    agent_registry.register(contract, adapter_factory)

# Auto-register on import
register_content_writer()
