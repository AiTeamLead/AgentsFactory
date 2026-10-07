import time
import asyncio
import traceback
from typing import Any, Callable

from agentkit.agents.base import BaseAgent
from agentkit.models.pipeline import AgentResult, PipelineState
from agentkit.models.topology import AgentConfig

class StandaloneAgentAdapter(BaseAgent):
    """Adapts a standalone Python function into the AgentKit BaseAgent interface.
    
    This allows existing scripts (like content_writer.py) to be executed
    by the AgentKit orchestrator without rewriting their business logic.
    """
    def __init__(self, config: AgentConfig, func: Callable, **kwargs):
        super().__init__(config=config, **kwargs)
        self._func = func

    async def execute(self, state: PipelineState, **kwargs: Any) -> AgentResult:
        start_time = time.time()
        
        try:
            # Map input parameters from state to the function.
            # original_input is a string in PipelineState, so parse it if it's JSON
            import json
            input_args = {}
            if state.original_input:
                try:
                    input_args = json.loads(state.original_input)
                except json.JSONDecodeError:
                    input_args = {"input": state.original_input}
                    
            # Merge with explicitly passed kwargs
            input_args.update(kwargs)
            
            if asyncio.iscoroutinefunction(self._func):
                result_data = await self._func(**input_args)
            else:
                # If it's a blocking synchronous function, ideally run in executor
                # but for simplicity in adaptation, we can call it directly or via to_thread
                result_data = await asyncio.to_thread(self._func, **input_args)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return AgentResult(
                agent_id=self.agent_id,
                status="success",
                output={"result": result_data},
                tokens_used=0, # Adapt as needed later
                cost_usd=0.0,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_details = traceback.format_exc()
            
            return AgentResult(
                agent_id=self.agent_id,
                status="failure",
                output={"error": str(e), "traceback": error_details},
                tokens_used=0,
                cost_usd=0.0,
                latency_ms=latency_ms
            )
