from pydantic import BaseModel
from typing import Optional, List

class UpdateProjectSchema(BaseModel):
  name: Optional[str]
  auto_edit: Optional[bool]
  instructions: Optional[List[str]]
