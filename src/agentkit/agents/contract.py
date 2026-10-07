from typing import Any, Dict, List
from pydantic import BaseModel, Field

class AgentContract(BaseModel):
    """The formal contract defining a registered agent's capabilities."""
    agent_id: str
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    safe_permissions: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    execution_mode: str = "sync"
    timeout: int = 60
    status: str = "active"
    error_handling: str = "propagate"
