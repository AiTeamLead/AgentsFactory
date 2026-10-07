from typing import Dict, Optional, Callable

from agentkit.agents.contract import AgentContract
from agentkit.agents.base import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._contracts: Dict[str, AgentContract] = {}
        self._adapters: Dict[str, Callable[..., BaseAgent]] = {}

    def register(self, contract: AgentContract, adapter_factory: Callable[..., BaseAgent]) -> None:
        """Register an agent contract and its corresponding adapter factory."""
        self._contracts[contract.agent_id] = contract
        self._adapters[contract.agent_id] = adapter_factory

    def get_contract(self, agent_id: str) -> Optional[AgentContract]:
        """Retrieve an agent contract by ID."""
        return self._contracts.get(agent_id)

    def get_adapter(self, agent_id: str) -> Optional[Callable[..., BaseAgent]]:
        """Retrieve the adapter factory for an agent by ID."""
        return self._adapters.get(agent_id)

    def list_agents(self) -> list[AgentContract]:
        """List all registered agent contracts."""
        return list(self._contracts.values())

# Global singleton registry
agent_registry = AgentRegistry()
