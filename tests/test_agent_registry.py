import pytest
from agentkit.agents.contract import AgentContract
from agentkit.agents.registry import AgentRegistry

def test_agent_registry():
    registry = AgentRegistry()
    
    contract = AgentContract(
        agent_id="test_agent",
        name="Test Agent",
        version="1.0.0",
        description="A test agent",
        input_schema={"test": {"type": "string"}},
        output_schema={"result": {"type": "string"}},
        capabilities=["testing"],
    )
    
    # Dummy adapter factory
    def factory():
        pass
        
    registry.register(contract, factory)
    
    assert registry.get_contract("test_agent") == contract
    assert registry.get_adapter("test_agent") == factory
    
    agents = registry.list_agents()
    assert len(agents) == 1
    assert agents[0].agent_id == "test_agent"
    assert "testing" in agents[0].capabilities
    
    assert registry.get_contract("unknown_agent") is None
