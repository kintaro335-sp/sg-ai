from pydantic import BaseModel

class SystemPrompt(BaseModel):
  section_name: str
  prompt: str
