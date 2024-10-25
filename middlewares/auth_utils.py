import os

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


users = MongoGenericRepository("BOB", "usuarios")

sessions = MongoGenericRepository("BOB", "sesiones")

SECRET_KEY = os.getenv("JWT_SECRET")

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = HTTPBearer(
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

def get_user(username: str):
  return users.get_by_query({"username": username})

def authenticate_user(username: str, password: str):
  user = get_user(username)
  if not user:
    return False
  if not verify_password(password, user['password']):
    return False
  return user

def create_access_token(data: dict, api_key: bool = False):
  to_encode = data.copy()
  new_session = { "session_id": to_encode['session_id'], "api_key": api_key, "expire_at": datetime.now(timezone.utc) + timedelta(days=7) }
  sessions.add(new_session)
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

def evaluate_session(session_id):
  session = sessions.get_by_query({ "session_id": session_id })
  if session:
    if session['api_key']:
      return True
    if session['expire_at'] > datetime.now(timezone.utc):
      return True
  return False

async def get_current_user(token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={},
  )
  try:
    payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")
    if user_id is None:
      raise credentials_exception
    if "session_id" not in payload:
      raise credentials_exception
    if not evaluate_session(payload["session_id"]):
      raise credentials_exception
    token_data = TokenData(user_id=user_id, session_id=payload.get("session_id"))
  except (InvalidTokenError, ValidationError):
      raise credentials_exception
  user = get_user(username=token_data.username)
  if user is None:
    raise credentials_exception
  return user

