from pydantic import BaseModel
from typing import List

class NewProjectSchema(BaseModel):
  name: str
  auto_edit: bool
  instructions: List[str]
