
from fastapi import APIRouter, Security

from services.auth_service import get_current_user

from services.wallet_service import wallet_service

wallet_router = APIRouter(prefix="/wallet", tags=["wallet_v1"])


@wallet_router.post("/init")
async def init_wallet(current_user: dict = Security(get_current_user)):
  return wallet_service.init_wallet(current_user["user_id"])


@wallet_router.get("/balance")
async def get_balance(current_user: dict = Security(get_current_user)):
  wallet_balance = wallet_service.get_balance(current_user["user_id"])
  return { "balance": wallet_balance }

