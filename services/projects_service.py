from fastapi import HTTPException
from variables_env import MONGO_DATABASE
from bson import ObjectId

from services.instructions_service import user_instructions
from schemas.body.video_ia.new_project import NewProjectSchema
from schemas.body.video_ia.update_project import UpdateProjectSchema
from db.mongo.mongo_generic_repository import MongoGenericRepository

import json


user_projects = MongoGenericRepository(MONGO_DATABASE, 'user_projects')


class ProjectsService:
  
  def __dump_new_project(self, new_project: NewProjectSchema):
    project_raw = new_project.model_dump_json()
    return json.loads(project_raw)

  def __dump_update_project(self, update_project: UpdateProjectSchema):
    project_raw = update_project.model_dump_json()
    return json.loads(project_raw)

  def add_project(self, new_project: NewProjectSchema, user_id: str):
    if user_projects.get_by_query({ "name": new_project.name, "user_id": user_id }) != None:
      raise HTTPException(status_code=400, detail="Project already exists")
    if new_project.name == "":
      raise HTTPException(status_code=400, detail="Project name cannot be empty")
    if new_project.name == 'transcription' or new_project.name == 'title':
      raise HTTPException(status_code=400, detail="Project name cannot be 'transcription'")
    new_project_doc = self.__dump_new_project(new_project)
    new_project_doc["user_id"] = user_id
    return user_projects.add(new_project_doc)

  def update_project(self, id_doc: str, update_project: UpdateProjectSchema):
    update_project_doc = self.__dump_update_project(update_project)
    user_projects.update_by_query({ "_id": id_doc }, update_project_doc)

  def get_project(self, name: str, user_id: str):
    project = user_projects.get_by_query({ "name": name, "user_id": user_id })
    if project == None:
      raise HTTPException(status_code=404)
    if user_id != project['user_id']:
      raise HTTPException(status_code=404)
    project["_id"] = str(project["_id"])
    instructions = []
    for instruction_id in project["instructions"]:
      instructions.append(str(instruction_id))
    project["instructions"] = instructions
    return project

  def get_project_j(self, user_id: str, name: str):
    project = user_projects.get_by_query({ "name": name, "user_id": user_id,  })
    return project

  def add_instruction_id(self, project_name: str, instruction_id: str, user_id: str):
    if not ObjectId.is_valid(instruction_id):
      raise HTTPException(status_code=400, detail="Invalid instruction id")
    instruction_objectid_id = ObjectId(instruction_id)
    if user_instructions.get_by_query({ "_id": instruction_objectid_id, "user_id": user_id }) == None:
      raise HTTPException(status_code=404, detail="Instruction not found")
    if user_projects.get_by_query({ "name": project_name, "user_id": user_id, "instructions": { "$in": [instruction_objectid_id] } }) != None:
      raise HTTPException(status_code=400, detail="Instruction already added")
    user_projects.collection.update_one({ "name": project_name, "user_id": user_id }, { "$push": { "instructions": instruction_objectid_id } })

  def remove_instruction_id(self, instruction_id: str):
    instruction_objectid_id = ObjectId(instruction_id)
    user_projects.collection.update_many({ "instructions": { "$in": [instruction_objectid_id] } }, { "$pull": { "instructions": instruction_objectid_id } })

  def get_project_by_id(self, id_doc: str, user_id: str):
    # chack is this user has access to this project
    project = user_projects.get(id_doc)
    if project["user_id"] != user_id:
      raise HTTPException(status_code=404)
    return user_projects.get(id_doc)

  def get_projects_by_user(self, user_id: str, page: int = 0, limit: int = 20):
    skip = page * limit
    projects_docs_raw = user_projects.get_all({ "user_id": user_id }, skip=skip, limit=limit)
    projects = []
    for project_doc in projects_docs_raw:
      project_doc["_id"] = str(project_doc["_id"])
      project_doc['instructions'] = [str(instruction_id) for instruction_id in project_doc['instructions']]
      projects.append(project_doc)
    return projects

  def delete_project(self, user_id: str, name: str):
    user_projects.delete({ "user_id": user_id, "name": name })


projects_service = ProjectsService()

