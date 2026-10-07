from agentkit.agents.registry import agent_registry
from agentkit.agents.contract import AgentContract
from agentkit.agents.adapter import StandaloneAgentAdapter
from agentkit.models.topology import AgentConfig
from agents.content_scheduler import run_content_scheduler

def register_content_scheduler_agent() -> None:
    """Registers the standalone content_scheduler agent into the AgentKit API Registry."""
    contract = AgentContract(
        agent_id="content_scheduler",
        name="Content Scheduler",
        version="1.0.0",
        description="Generates, queues, and schedules LinkedIn posts using Ocoya API and AI copy generation.",
        input_schema={
            "action": {
                "type": "string",
                "enum": ["generate", "calendar", "schedule_week"],
                "default": "generate",
                "description": "The action to perform."
            },
            "pillar": {
                "type": "string",
                "default": None,
                "description": "Content pillar for generation (if action is generate)"
            },
            "posts_per_day": {
                "type": "integer",
                "default": 1,
                "description": "Number of posts to schedule per day (if action is schedule_week)"
            },
            "dry_run": {
                "type": "boolean",
                "default": False,
                "description": "If True, simulates scheduling without making external API calls to Ocoya."
            }
        },
        output_schema={
            "action": {"type": "string"},
            "post": {"type": "string", "description": "Present if action is generate"},
            "calendar": {"type": "object", "description": "Present if action is calendar"},
            "scheduled": {"type": "integer", "description": "Present if action is schedule_week"},
            "posts": {"type": "array", "description": "Present if action is schedule_week"},
            "dry_run": {"type": "boolean"}
        },
        capabilities=["social_media_scheduling", "content_generation", "api_integration"],
        required_tools=[],
        required_permissions=["social_media_write"],
        safe_permissions=["agent:execute_safe"],
        risk_level="HIGH",
        execution_mode="sync"
    )

    def adapter_factory(config: AgentConfig = None, **kwargs) -> StandaloneAgentAdapter:
        if not config:
            config = AgentConfig(agent_id=contract.agent_id, role="social_media_manager", model="local")
        return StandaloneAgentAdapter(config=config, func=run_content_scheduler, **kwargs)

    agent_registry.register(contract, adapter_factory)

# Auto-register on import
register_content_scheduler_agent()
