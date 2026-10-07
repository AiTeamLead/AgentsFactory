"""Agent API routes — register, list, run individual agents."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from agentkit.api.models import (
    AgentCreateRequest,
    AgentResponse,
    AgentRunRequest,
    AgentRunResponse,
    ErrorResponse,
)
from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent, EvaluatorAgent
from agentkit.config import settings
from agentkit.models.topology import AgentConfig
from agentkit.agents.registry import agent_registry
from agentkit.api.security import get_current_user, authorize_agent_execution, User
from fastapi import Depends

# Import pilot registration to ensure it's loaded
try:
    import agentkit.agents.content_writer_registration
except ImportError:
    pass

try:
    import agentkit.agents.lead_loader_registration
except ImportError:
    pass

try:
    import agentkit.agents.content_scheduler_registration
except ImportError:
    pass

try:
    import agentkit.agents.daily_briefing_registration
except ImportError:
    pass

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory agent registry for backward compatibility with old tests
_registered_agents: dict[str, Any] = {}

def _create_agent(config: AgentCreateRequest) -> Any:
    """Create an agent from request config."""
    agent_config = AgentConfig(
        agent_id=config.agent_id,
        role=config.role,
        model=config.model,
        system_prompt=config.system_prompt,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        tools=config.tools,
        allowed_tools=config.allowed_tools,
    )
    role_map = {
        "researcher": ResearcherAgent,
        "analyzer": AnalyzerAgent,
        "writer": WriterAgent,
        "evaluator": EvaluatorAgent,
    }
    agent_class = role_map.get(config.role, ResearcherAgent)
    return agent_class(config=agent_config)

@router.post("/register", response_model=AgentResponse, responses={400: {"model": ErrorResponse}})
async def register_agent(request: AgentCreateRequest) -> dict:
    """Register an agent for use in pipelines."""
    if not request.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    agent = _create_agent(request)
    _registered_agents[request.agent_id] = agent

    return {
        "agent_id": request.agent_id,
        "role": request.role,
        "model": request.model,
        "status": "registered",
    }

@router.get("/", response_model=list[AgentResponse])
async def list_agents() -> list[dict]:
    """List all registered agents."""
    agents = []
    
    # 1. Add modern contracted agents
    for contract in agent_registry.list_agents():
        agents.append({
            "agent_id": contract.agent_id,
            "name": contract.name,
            "version": contract.version,
            "description": contract.description,
            "role": "",
            "model": "",
            "status": contract.status,
            "input_schema": contract.input_schema,
            "output_schema": contract.output_schema,
            "capabilities": contract.capabilities,
            "required_tools": contract.required_tools,
            "required_permissions": contract.required_permissions,
            "execution_mode": contract.execution_mode
        })
        
    # 2. Add legacy test agents
    for agent_id, agent in _registered_agents.items():
        if not agent_registry.get_contract(agent_id):
            agents.append({
                "agent_id": agent_id,
                "role": agent.config.role,
                "model": agent.config.model,
                "status": "registered",
            })
            
    return agents

@router.get("/{agent_id}", response_model=AgentResponse, responses={404: {"model": ErrorResponse}})
async def get_agent(agent_id: str) -> dict:
    """Get agent details."""
    contract = agent_registry.get_contract(agent_id)
    if contract:
        return {
            "agent_id": contract.agent_id,
            "name": contract.name,
            "version": contract.version,
            "description": contract.description,
            "role": "",
            "model": "",
            "status": contract.status,
            "input_schema": contract.input_schema,
            "output_schema": contract.output_schema,
            "capabilities": contract.capabilities,
            "required_tools": contract.required_tools,
            "required_permissions": contract.required_permissions,
            "execution_mode": contract.execution_mode
        }
        
    if agent_id in _registered_agents:
        agent = _registered_agents[agent_id]
        return {
            "agent_id": agent_id,
            "role": agent.config.role,
            "model": agent.config.model,
            "status": "registered",
        }
        
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

@router.post("/{agent_id}/run", response_model=AgentRunResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def run_agent(agent_id: str, request: AgentRunRequest, current_user: User = Depends(get_current_user)) -> dict:
    """Run a single agent with the given input."""
    # Handle modern contracted agents
    contract = agent_registry.get_contract(agent_id)
    if contract:
        # Authorization Phase
        authorize_agent_execution(contract, request.input, current_user)
        
        try:
            adapter_factory = agent_registry.get_adapter(agent_id)
            agent = adapter_factory()
            
            from agentkit.models.pipeline import PipelineState
            # PipelineState expects original_input to be a string
            state = PipelineState(original_input=request.input)
            result = await agent.execute(state, **request.context)
            
            return {
                "agent_id": agent_id,
                "status": result.status.value if hasattr(result.status, "value") else str(result.status),
                "output": result.output,
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
                "latency_ms": result.latency_ms,
                "confidence": getattr(result, "confidence", 0.0),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    # Handle legacy test agents
    if agent_id not in _registered_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    if not settings.openrouter_api_key:
        raise HTTPException(status_code=401, detail="OpenRouter API key not configured")

    agent = _registered_agents[agent_id]
    try:
        from agentkit.models.pipeline import PipelineState
        state = PipelineState(original_input=request.input)
        result = await agent.execute(state, **request.context)

        return {
            "agent_id": agent_id,
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "output": result.output,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "latency_ms": result.latency_ms,
            "confidence": getattr(result, "confidence", 0.0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@router.delete("/{agent_id}")
async def unregister_agent(agent_id: str) -> dict:
    """Unregister an agent."""
    if agent_id in _registered_agents:
        del _registered_agents[agent_id]
        return {"status": "unregistered", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
