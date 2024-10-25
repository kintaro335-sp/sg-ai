from pydantic import BaseModel, Field
from typing import Optional, List
from schemas.body.video_ia.system_prompt import SystemPrompt
from schemas.body.video_ia.crew_schema import CrewStructureSchema

class UpdateInstructionSchema(BaseModel):
  name: Optional[str] = Field(None,nullable=True)
  file_prefix: Optional[str] = Field(None,nullable=True)
  type: Optional[str] = Field(None,nullable=True)
  system_prompt: Optional[str] = Field(None,nullable=True)
  system_prompts: Optional[List[SystemPrompt]] = Field(None,nullable=True)
  crew: Optional[CrewStructureSchema] = Field(None,nullable=True)
  agent: Optional[str] = Field(None,nullable=True)
  thread_id: Optional[str] = Field(None, nullable=True)
