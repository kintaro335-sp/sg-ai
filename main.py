import uvicorn

from fastapi import FastAPI, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from services.auth_service import get_current_user
from middlewares.active_license_middleware import active_license_middleware
# routers
from routers.v1.v1_router import v1_router

app = FastAPI(
  title="mmonk",
  version="0.0.1",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# @app.middleware("http")
# async def active_license_middleware_w(request: Request, call_next):
#   return await active_license_middleware(request, call_next)

app.include_router(v1_router)

@app.get("/")
async def root():
  return {"message": "Hello World"}


if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8080)
