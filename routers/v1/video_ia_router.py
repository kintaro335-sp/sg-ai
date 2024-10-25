
from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks, Security, Query
from fastapi.responses import PlainTextResponse
from services.auth_service import get_current_user

from services.video_ia_service import video_ia_service
from services.jobs_service import jobs_service
from services.projects_service import projects_service
from services.instructions_service import instructions_service

# schemas
from schemas.body.video_ia.new_project import NewProjectSchema
from schemas.body.video_ia.new_instruction import NewInstructionSchema
from schemas.body.video_ia.update_project import UpdateProjectSchema
from schemas.body.video_ia.update_instruction import UpdateInstructionSchema


video_ia_router = APIRouter(prefix="/video_ia", tags=["video_ia_v1"])


@video_ia_router.post("/process_file/{project_name}", description="upload a multimedia file and process it")
async def upload_file(project_name: str, file: UploadFile, background_tasks: BackgroundTasks, current_user: dict = Security(get_current_user)):
  # if not video_ia_service.is_video(file):
  #   raise HTTPException(status_code=415, detail="File not supported")
  
  return video_ia_service.add_process_task(background_tasks, file, current_user["user_id"], project_name)

@video_ia_router.post("/file/initialize/{project_name}/{file_name}", description="initialize a file state to upload files bigger than 100MB")
async def initialize_file_state(project_name: str, file_name: str, size: int = Query(0, type='int', alias="size", gt=0), current_user: dict = Security(get_current_user)):
  return video_ia_service.initialize_file_state(current_user["user_id"], project_name, file_name, size)

@video_ia_router.post("/file/write_blob/{project_name}/{file_name}/{position}", description="upload blob of files")
async def write_file_blob(project_name: str, file_name: str, position: int, file: UploadFile, current_user: dict = Security(get_current_user)):
  return video_ia_service.write_file_blob(current_user["user_id"], project_name, file_name, position, file.file.read())

@video_ia_router.post("/file/finish/{project_name}/{file_name}", description="indicates the end of the file upload to start processing")
async def finish_file(project_name: str, file_name: str, background_tasks: BackgroundTasks, current_user: dict = Security(get_current_user)):
  return video_ia_service.finish_file(current_user["user_id"], project_name, file_name, background_tasks)

@video_ia_router.get("/projects", description="get all projects by user; projects is to group AI instructions in one project and process the multimedia file")
async def get_projects(current_user: dict = Security(get_current_user), limit: int = Query(20, ge=5), page: int = Query(1, ge=1)):
  return projects_service.get_projects_by_user(current_user["user_id"], page - 1, limit)

@video_ia_router.post("/projects", description="create a new project")
async def create_project(body: NewProjectSchema, current_user: dict = Security(get_current_user)):
  result = projects_service.add_project(body, current_user["user_id"])
  return { "data": body, "id": str(result.inserted_id) }

@video_ia_router.get("/projects/{project_name}", description="get a project by name")
async def get_project(project_name: str, current_user: dict = Security(get_current_user)):
  project = projects_service.get_project(project_name, current_user["user_id"])
  if project is None:
    raise HTTPException(status_code=404, detail="Project not found")
  return project

@video_ia_router.put("/projects/{project_name}", description="update a project by name")
async def update_project(project_name: str, body: UpdateProjectSchema, current_user: dict = Security(get_current_user)):
  projects_service.update_project(project_name, body, current_user["user_id"])
  return { 'message': 'project updated' }

@video_ia_router.put("/projects/{project_name}/instruction/{instruction_id}", description="add an instruction to a project")
async def update_project_instruction(project_name: str, instruction_id: str, current_user: dict = Security(get_current_user)):
  projects_service.add_instruction_id(project_name, instruction_id, current_user["user_id"])
  return { 'message': 'project updated' }

@video_ia_router.delete("/projects/{project_name}", description="delete a project by name")
async def delete_project(project_name: str, current_user: dict = Security(get_current_user)):
  projects_service.delete_project(project_name, current_user["user_id"])
  return { 'message': 'project deleted' }

@video_ia_router.get("/instructions", description="get all instructions by user")
async def get_instructions(current_user: dict = Security(get_current_user), limit: int = Query(20), page: int = Query(1)):
  return instructions_service.get_instructions(current_user["user_id"], page - 1, limit)


@video_ia_router.post("/instructions", description="create a new instruction")
async def create_instruction(body: NewInstructionSchema, current_user: dict = Security(get_current_user)):
  result = instructions_service.add_instruction(body, current_user["user_id"])
  return { "data":body, "id": str(result.inserted_id) }

@video_ia_router.put("/instructions/{id_doc}", description="update an instruction by id")
async def update_instruction(id_doc: str, body: UpdateInstructionSchema, current_user: dict = Security(get_current_user)):
  instructions_service.update_instruction(id_doc, body, current_user["user_id"])
  return { 'message': 'instruction updated' }

@video_ia_router.get("/instructions/{id_doc}", description="get an instruction by id")
async def get_instruction(id_doc: str, current_user: dict = Security(get_current_user)):
  instruction = instructions_service.get_instruction_by_id(id_doc, current_user["user_id"])
  if instruction is None:
    raise HTTPException(status_code=404, detail="Instruction not found")
  return instruction

@video_ia_router.delete("/instructions/{id_doc}", description="delete an instruction by id")
async def delete_instruction(id_doc: str, current_user: dict = Security(get_current_user)):
  projects_service.remove_instruction_id(id_doc)
  instructions_service.delete_instruction(current_user["user_id"], id_doc)
  return { 'message': 'instruction deleted' }

@video_ia_router.get("/jobs", description="get all jobs by user")
async def get_jobs(current_user: dict = Security(get_current_user), limit: int = Query(20), page: int = Query(1)):
  return jobs_service.get_jobs(current_user["user_id"], page - 1, limit)

@video_ia_router.get("/jobs/{job_id}", description="get a job by id")
async def get_job(job_id: str, current_user: dict = Security(get_current_user)):
  job = jobs_service.get_job(current_user["user_id"], job_id)
  if job is None:
    raise HTTPException(status_code=404, detail="Job not found")
  return job


@video_ia_router.get("/jobs-results/{job_id}", description="get a job results by id")
async def get_job_results(job_id: str, current_user: dict = Security(get_current_user)):
  job = jobs_service.get_jobs_results(current_user["user_id"], job_id)
  if job is None:
    raise HTTPException(status_code=404, detail="Job not found")
  return job

@video_ia_router.get("/jobs-results/{job_id}/{result_key}", description="get a job results by id and result key; response is a plain text file")
async def get_job_result_file(job_id: str, result_key: str, current_user: dict = Security(get_current_user)):
  result = jobs_service.download_job_result_file(current_user["user_id"], job_id, result_key)
  if result == None:
    raise HTTPException(status_code=404, detail="Job not found")

  return PlainTextResponse(result, media_type='plain/text')
