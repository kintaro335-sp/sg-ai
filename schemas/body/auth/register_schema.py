from pydantic import BaseModel

class RegisterSchema(BaseModel):
  username: str
  email: str
  password: str
