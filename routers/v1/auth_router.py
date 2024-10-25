from fastapi import APIRouter
from services.auth_service import authenticate_user, create_access_token, get_password_hash, get_current_user, logout_user, Token, users
from fastapi import Depends, HTTPException, Security, Query 
from schemas.body.auth.register_schema import RegisterSchema
from schemas.body.auth.login_schema import LoginSchema

import uuid

auth_router = APIRouter(prefix='/auth', tags=["auth_v1"])

@auth_router.post("/register", response_model=Token)
async def signup(body: RegisterSchema):
  exist_user = users.get_by_query({"email": body.email})
  exist_user_username = users.get_by_query({"username": body.username})
  if exist_user:
    raise HTTPException(status_code=400, detail="Email already registered")
  if exist_user_username:
    raise HTTPException(status_code=400, detail="Username already registered")

  hashed_password = get_password_hash(body.password)
  user = { "user_id": str(uuid.uuid4()), "username": body.username, "email": body.email, "password": hashed_password, "license_enabled": False }
  users.add(user)
  access_token = create_access_token(
    data=user,
  )
  return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/token/username", response_model=Token)
async def login_for_access_token(form_data: LoginSchema = Depends(), api_key: bool = Query(default=False, alias="api_key")):
  user = authenticate_user(form_data.username, form_data.password)
  if not user:
    raise HTTPException(status_code=400, detail="Incorrect username or password")
  # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={ "user_id": user["user_id"], "session_id": str(uuid.uuid4())}, api_key=api_key
  )
  return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
  return logout_user(current_user["session_id"])

@auth_router.get("/users/me")
async def read_users_me(current_user: dict = Security(get_current_user)):
  return { "session_id": current_user["session_id"], "user_id": current_user["user_id"], "username": current_user["username"] }
