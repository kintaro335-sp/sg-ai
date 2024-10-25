from fastapi import Request, status
from fastapi.responses import JSONResponse
from services.auth_service import get_current_user_middleware

v1_video_ia_base = '/v1/video_ia'

routes_restrcted = [
  f'{v1_video_ia_base}/process_file',
  f'{v1_video_ia_base}/file/',
]

def is_path_protected(path: str):
  for route in routes_restrcted:
    if path.startswith(route):
      return True
  return False

async def active_license_middleware(request: Request, call_next):
  error_response = JSONResponse(
    status_code=status.HTTP_403_FORBIDDEN,
    content={"message": "License not active"}
  )

  if not is_path_protected(request.scope.get('path')):
    return await call_next(request)

  authorization_header = request.headers.get("Authorization")
  if authorization_header == None:
    return error_response

  user = get_current_user_middleware(str(authorization_header))
  if user == None:
    return error_response

  if user.get('license_enabled') == False or user.get('license_enabled') == None:
    return error_response

  return await call_next(request)
