from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class NewJobSchema(BaseModel):
  job_id: str
  project_name: str
  user_id: str
  file_name: str
  file_path: str
  cost: int
  status: Literal["pending", "running", "success", "failed"]
  step: Literal['initializing', 'converting', 'transcribing', 'processing', 'saving', 'finished']
  created_at: datetime
  finished_at: datetime
  results: dict
  file_prefix: dict
  error: str
  error_code: int
