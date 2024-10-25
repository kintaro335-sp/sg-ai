from fastapi import HTTPException
from variables_env import MONGO_DATABASE
from bson import ObjectId
from db.mongo.mongo_generic_repository import MongoGenericRepository

from schemas.body.video_ia.update_instruction import UpdateInstructionSchema
from schemas.body.video_ia.new_instruction import NewInstructionSchema

import json

user_instructions = MongoGenericRepository(MONGO_DATABASE, 'user_instructions')

class InstructionsService:

  def __dump_new_instruction(self, instruction: NewInstructionSchema):
    instruction_raw = instruction.model_dump_json()
    return json.loads(instruction_raw)

  def __dump_update_instruction(self, instruction: UpdateInstructionSchema):
    instruction_raw = instruction.model_dump_json()
    return json.loads(instruction_raw)

  def add_instruction(self, instruction: NewInstructionSchema, user_id: str):
    instruction_doc = self.__dump_new_instruction(instruction)
    instruction_doc["user_id"] = user_id
    return user_instructions.add(instruction_doc)

  def update_instruction(self, id_doc: str, new_instruction: UpdateInstructionSchema, user_id: str):
    # check is this user own this instruction
    instruction = user_instructions.get(id_doc)
    if instruction == None:
      raise HTTPException(status_code=404)
    if instruction["user_id"] != user_id:
      raise HTTPException(status_code=404)
    updated_instruction = self.__dump_update_instruction(new_instruction)
    updated_instruction["_id"] = ObjectId(id_doc)
    keys=list(updated_instruction.keys())
    for key in keys:
      if updated_instruction[key] == None:
        del updated_instruction[key]
    user_instructions.update(updated_instruction)

  def update_instruction_thread_id_j(self, id_doc: str, thread_id: str):
    # check is this user own this instruction
    user_instructions.update({"_id": ObjectId(id_doc), "thread_id": thread_id})

  def get_instruction_thread_id_j(self, id_doc: str):
    instruction_doc = user_instructions.get(id_doc)
    if instruction_doc == None:
      return None
    try:
      return instruction_doc["thread_id"]
    except KeyError:
      return None

  def get_instruction_by_id(self, id_doc: str, user_id: str):
    # chack is this user has access to this project
    instruction = user_instructions.get(id_doc)
    if instruction == None:
      raise HTTPException(status_code=404)
    if instruction["user_id"] != user_id:
      raise HTTPException(status_code=404)
    instruction['_id'] = str(instruction['_id'])
    return instruction

  def get_instruction_by_name_j(self, id_doc: str):
    return user_instructions.get(id_doc)

  def get_instructions(self, user_id: str, page: int = 0, limit: int = 20):
    skip = page * limit
    docs_raw = user_instructions.get_all({"user_id": user_id}, skip=skip, limit=limit)
    docs = []
    for doc in docs_raw:
      doc['_id'] = str(doc['_id'])
      docs.append(doc)
    return docs

  def get_instructions_by_user_all_projects_j(self, user_id: str):
    docs_raw = user_instructions.get_all({"user_id": user_id, "all_projects": True})
    docs = []
    for doc in docs_raw:
      doc['_id'] = str(doc['_id'])
      docs.append(doc)
    return docs

  def get_instructions_j(self, ids_docs: list[ObjectId]):
    docs = []
    for id in ids_docs:
      doc = user_instructions.get(str(id))
      doc['_id'] = str(doc['_id'])
      docs.append(doc)
    return docs

  def delete_instruction(self, user_id: str, id_doc: str):
    # check is this user own this instruction
    instruction = user_instructions.get_by_query({ "_id": ObjectId(id_doc), "user_id": user_id })
    if instruction == None:
      raise HTTPException(status_code=404)
    user_instructions.delete_by_id(id_doc)

instructions_service = InstructionsService()
