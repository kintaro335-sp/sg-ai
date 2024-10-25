from typing import List, Literal, Optional
from pydantic import BaseModel
from schemas.body.video_ia.system_prompt import SystemPrompt
from schemas.body.video_ia.crew_schema import CrewStructureSchema

class NewInstructionSchema(BaseModel):
  name: str
  file_prefix: str
  type: Literal['single', 'compound', 'chain', 'crew', 'agent']
  system_prompt: Optional[str] = None
  system_prompts: Optional[List[SystemPrompt]] = None
  crew: Optional[CrewStructureSchema] = None
  agent: Optional[str] = None
  thread_id: Optional[str] = None
