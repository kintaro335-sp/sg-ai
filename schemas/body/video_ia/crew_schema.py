from typing import List, Literal, Optional
from pydantic import BaseModel

class AgentSchema(BaseModel):
  name: str
  role: str
  goal: str
  memory: bool
  allow_delegation: bool
  backstory: str

class TaskSchema(BaseModel):
  name: str
  agent: str
  description: str
  expected_output: str
  

class CrewStructureSchema(BaseModel):
  process: Optional[Literal['sequential', 'hierarchical']] = 'sequential'
  agents: List[AgentSchema]
  tasks: List[TaskSchema]
