from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ExecutionPlan(BaseModel):
    plan: List[str] = Field(
        description="A list of steps to execute in order to answer a prompt."
    )

class ToolDecision(BaseModel):
    tool: str
    query: str

class QueryRequest(BaseModel):
    query: str
    history: List[Dict[str, Any]] = []

class QueryResponse(BaseModel):
    answer: str
    observations: List[Dict[str, Any]]
