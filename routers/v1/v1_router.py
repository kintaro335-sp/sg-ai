
from fastapi import APIRouter
import constants
# routers
from routers.v1.auth_router import auth_router
from routers.v1.insuretech_router import insuretech_router
from routers.v1.video_ia_router import video_ia_router
from routers.v1.wallet_router import wallet_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router)
v1_router.include_router(insuretech_router)
v1_router.include_router(video_ia_router)
v1_router.include_router(wallet_router)