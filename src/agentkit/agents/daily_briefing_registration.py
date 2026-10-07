from agentkit.agents.registry import agent_registry
from agentkit.agents.contract import AgentContract
from agentkit.agents.adapter import StandaloneAgentAdapter
from agentkit.models.topology import AgentConfig
from agents.daily_briefing import generate_briefing

def register_daily_briefing() -> None:
    """Registers the standalone daily_briefing agent into the AgentKit API Registry."""
    contract = AgentContract(
        agent_id="daily_briefing",
        name="Daily Briefing",
        version="1.0.0",
        description="Generates a morning briefing including automation health, content drafted, and leads found.",
        input_schema={},
        output_schema={
            "result": {"type": "string"}
        },
        capabilities=["reporting", "analytics"],
        required_tools=[],
        required_permissions=["agent:execute_safe"],
        safe_permissions=["agent:execute_safe"],
        risk_level="LOW",
        execution_mode="sync"
    )

    def adapter_factory(config: AgentConfig = None, **kwargs) -> StandaloneAgentAdapter:
        if not config:
            config = AgentConfig(agent_id=contract.agent_id, role="reporter", model="local")
        return StandaloneAgentAdapter(config=config, func=generate_briefing, **kwargs)

    agent_registry.register(contract, adapter_factory)

# Auto-register on import
register_daily_briefing()
