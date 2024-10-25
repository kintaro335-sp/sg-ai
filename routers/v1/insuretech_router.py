from fastapi import APIRouter, UploadFile, HTTPException, Query, Security
from services.auth_service import get_current_user
from services.insuretech_service import insuretech_service


insuretech_router = APIRouter(prefix='/insuretech', tags=["insuretech_v1"])

@insuretech_router.get("/get_thread_list")
def get_thread_list(current_user: dict = Security(get_current_user)):
  try:
    result = insuretech_service.get_thread_list()
    return { "data": result }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@insuretech_router.post("/get_pdf_text")
async def get_pdf_text(pdf_file: UploadFile, one_page = False, current_user: dict = Security(get_current_user)):
  if not insuretech_service.is_pdf(pdf_file):
    raise HTTPException(status_code=415, detail="File not supported")

  try:
    result = insuretech_service.get_pdf_text(pdf_file, one_page)  
    return { "data": result }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@insuretech_router.post("/get_pdf_data")
async def get_pdf_data(pdf_file: UploadFile, current_user: dict = Security(get_current_user), insurance: str = Query(alias='insurance'), ramo: str = Query(alias='ramo')):
  if not insuretech_service.is_pdf(pdf_file):
    raise HTTPException(status_code=415, detail="File not supported")

  try:
    result = insuretech_service.get_pdf_data(pdf_file, insurance, ramo)  
    return { "data": result }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


