import pytest
import json
from fastapi.testclient import TestClient

from agentkit.api.app import app
from agentkit.models.pipeline import PipelineState
from agentkit.models.topology import AgentConfig
from agentkit.agents.adapter import StandaloneAgentAdapter

def sample_sync_func(arg1: str, arg2: int = 5):
    return {"message": f"Hello {arg1}, you have {arg2} items."}

async def sample_async_func(arg1: str, arg2: int = 5):
    return {"message": f"Async hello {arg1}, you have {arg2} items."}

def error_func():
    raise ValueError("Something went wrong")

@pytest.mark.asyncio
async def test_standalone_adapter_sync():
    config = AgentConfig(agent_id="sync_test", role="test")
    adapter = StandaloneAgentAdapter(config=config, func=sample_sync_func)
    
    state = PipelineState(original_input=json.dumps({"arg1": "Alice", "arg2": 10}))
    result = await adapter.execute(state)
    
    assert result.status == "success"
    assert result.output["result"]["message"] == "Hello Alice, you have 10 items."

@pytest.mark.asyncio
async def test_standalone_adapter_async():
    config = AgentConfig(agent_id="async_test", role="test")
    adapter = StandaloneAgentAdapter(config=config, func=sample_async_func)
    
    state = PipelineState(original_input=json.dumps({"arg1": "Bob"}))
    result = await adapter.execute(state)
    
    assert result.status == "success"
    assert result.output["result"]["message"] == "Async hello Bob, you have 5 items."

@pytest.mark.asyncio
async def test_standalone_adapter_error():
    config = AgentConfig(agent_id="error_test", role="test")
    adapter = StandaloneAgentAdapter(config=config, func=error_func)
    
    state = PipelineState(original_input=json.dumps({}))
    result = await adapter.execute(state)
    
    assert result.status == "failure"
    assert "Something went wrong" in result.output["error"]

def test_api_content_writer_execution():
    client = TestClient(app)
    
    # 1. Discover agent
    response = client.get("/agents/")
    assert response.status_code == 200
    agents = response.json()
    assert any(a["agent_id"] == "content_writer" for a in agents)
    
    # 2. Get agent details
    response = client.get("/agents/content_writer")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "content_writer"
    assert "content_generation" in data["capabilities"]
    
    # 3. Execute agent (use dry_run to prevent DB clutter)
    payload = {
        "input": json.dumps({
            "pillar": "tips_tutorial",
            "platform": "linkedin",
            "topic": "test automation",
            "count": 1,
            "dry_run": True
        })
    }
    
    headers={"Authorization": "Bearer test-token-safe"} # safe executes dry run correctly
    response = client.post("/agents/content_writer/run", json=payload, headers=headers)
    if response.status_code != 200:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 200
    result = response.json()
    
    assert result["agent_id"] == "content_writer"
    assert result["status"] == "success"
    
    output = result["output"]["result"]
    assert isinstance(output, list)
    assert len(output) == 1
    assert "title" in output[0]
    assert "content" in output[0]

def test_api_content_writer_execution_dangerous():
    client = TestClient(app)
    payload = {
        "input": json.dumps({
            "pillar": "tips_tutorial",
            "platform": "linkedin",
            "topic": "test automation",
            "count": 1,
            "dry_run": False
        })
    }
    
    # Needs database_write permission
    headers={"Authorization": "Bearer test-token-safe"}
    response = client.post("/agents/content_writer/run", json=payload, headers=headers)
    assert response.status_code == 403
