import os
from variables_env import MONGO_DATABASE, JWT_SECRET, JWT_ALGORITHM
from typing import Literal
from datetime import datetime, timedelta, timezone
from typing import Annotated
from db.mongo.mongo_generic_repository import MongoGenericRepository

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError


users = MongoGenericRepository(MONGO_DATABASE, "usuarios")

sessions = MongoGenericRepository(MONGO_DATABASE, "sesiones")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_scheme = HTTPBearer(
    bearerFormat="token",
)

class Token(BaseModel):
  access_token: str
  token_type: str


class TokenData(BaseModel):
  user_id: str
  session_id: str


class User(BaseModel):
  username: str
  email: str | None = None
  full_name: str | None = None
  disabled: bool | None = None


class UserInDB(User):
  hashed_password: str

def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
  return pwd_context.hash(password)

def get_user(user: str, type: Literal['user_id', 'email', 'username'] = 'username'):
  query = {}
  query[type] = user
  return users.get_by_query(query)


def authenticate_user(user: str, password: str, type: Literal['user_id', 'email', 'username'] = 'username'):
  user = get_user(user, type)
  if not user:
    return False
  if not verify_password(password, user['password']):
    return False
  return user

def create_access_token(data: dict, api_key: bool = False):
  to_encode = data.copy()
  new_session = { "session_id": to_encode['session_id'], "api_key": api_key, "expire_at": datetime.now(timezone.utc) + timedelta(days=7) }
  sessions.add(new_session)
  encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
  return encoded_jwt

def evaluate_session(session_id):
  session = sessions.get_by_query({ "session_id": session_id })
  # print(type(session['expire_at']))
  if session:
    if session['api_key']:
      return True
    if session['expire_at'].astimezone(timezone.utc) > datetime.now(timezone.utc):
      return True
  if session != None:
    sessions.delete({ "session_id": session_id })

  return False

async def get_current_user(token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]):
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={},
  )
  try:
    payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    user_id: str = payload.get("user_id")
    if user_id is None:
      raise credentials_exception
    if "session_id" not in payload:
      raise credentials_exception
    if not evaluate_session(payload["session_id"]):
      raise credentials_exception
    token_data = TokenData(user_id=user_id, session_id=payload.get("session_id"))
  except (InvalidTokenError, ValidationError):
      raise credentials_exception
  user = get_user(token_data.user_id, 'user_id')
  user['_id'] = str(user['_id'])
  user['session_id'] = token_data.session_id
  if user is None:
    raise credentials_exception
  return user

def get_current_user_middleware(token: str):
  try:
    token = token.split(" ")[1]
  except IndexError:
    pass
  try:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    user_id: str = payload.get("user_id")
    if user_id == None:
      return None
    if "session_id" not in payload:
      return None
    if not evaluate_session(payload["session_id"]):
      return None
    token_data = TokenData(user_id=user_id, session_id=payload.get("session_id"))
  except (InvalidTokenError, ValidationError):
      return None
  user = get_user(token_data.user_id, 'user_id')
  if user == None:
    return None
  user['_id'] = str(user['_id'])
  user['session_id'] = token_data.session_id
  return user

def logout_user(session_id):
  sessions.delete({ "session_id": session_id })
  return { "message": "User logged out successfully" }
