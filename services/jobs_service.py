from fastapi import HTTPException
from variables_env import MONGO_DATABASE
from typing import Literal
from schemas.body.jobs.new_job_schema import NewJobSchema
from db.mongo.mongo_generic_repository import MongoGenericRepository

from datetime import datetime

import uuid
import json

jobs_repository = MongoGenericRepository(MONGO_DATABASE, "user_jobs")

results_repository = MongoGenericRepository(MONGO_DATABASE, "job_results")

class JobsService:

  def __dump_job(self, new_job: NewJobSchema):
    new_job_raw = new_job.model_dump_json()
    new_job_doc = json.loads(new_job_raw)
    new_job_doc["created_at"] = datetime.strptime(new_job_doc["created_at"], "%Y-%m-%dT%H:%M:%S.%f")
    new_job_doc["finished_at"] = datetime.strptime(new_job_doc["finished_at"], "%Y-%m-%dT%H:%M:%S.%f")
    return new_job_doc

  def create_job(self, user_id: str, file_name: str, file_path: str, project_name: str):

    job_id = str(uuid.uuid4())

    new_job = NewJobSchema(
      job_id=job_id,
      project_name=project_name,
      user_id=user_id,
      file_name=file_name,
      file_path=file_path,
      status="pending",
      cost=0,
      step="initializing",
      results={},
      file_prefix={},
      created_at=datetime.now(),
      finished_at=datetime.now(),
      error="",
      error_code=0
    )
    self.add_job(new_job)
    return job_id

  def add_job(self, new_job: NewJobSchema):
    jobs_repository.add(self.__dump_job(new_job))    

  def get_job(self, user_id: str, job_id: str):
    # check if user is owner
    if jobs_repository.get_by_query({"user_id": user_id, "job_id": job_id}) == None:
      raise HTTPException(status_code=404)
    job_doc = jobs_repository.get_by_query({"user_id": user_id, "job_id": job_id})
    job_doc["_id"] = str(job_doc["_id"])

    results_keys = list(job_doc["results"].keys())
    job_doc["results"] = results_keys

    return job_doc

  def update_job_status(self, user_id: str, job_id: str, status: Literal["pending", "running", "success", "failed"]):
    jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, {"status": status})

  def update_job_error(self, user_id: str, job_id: str, error: str, error_code: int):
    jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, {"error": error, "error_code": error_code})

  def update_job_results(self, user_id: str, job_id: str, results: dict):
    jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id},  {"results": results})

  def update_job_result(self, user_id: str, job_id: str, key: str, result: dict):
    doc_result = results_repository.add({ "user_id": user_id, "job_id": job_id, "data": result['result'], "created_at": datetime.now() })
    jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, {f"results.{key}": doc_result.inserted_id})
    if result['file_prefix'] != '':
      jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, {f"file_prefix.{key}": result['file_prefix']})

  def update_job_step(self, user_id: str, job_id: str, step: Literal['initializing', 'converting', 'transcribing', 'processing', 'saving', 'finished']):
    jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, { "step": step })
    if step == 'finished':
      jobs_repository.update_by_query({"user_id": user_id, "job_id": job_id}, { "finished_at": datetime.now() })

  def get_jobs(self, user_id: str, page: int = 0, limit: int = 20):
    skip = page * limit
    jobs_docs_raw = jobs_repository.get_all({"user_id": user_id}, skip=skip, limit=limit)
    jobs_docs = []
    for job_doc in jobs_docs_raw:
      job_doc["_id"] = str(job_doc["_id"])
      result_str = []
      for result in job_doc["results"]:
        result_str.append(str(result))
      job_doc["results"] = result_str
      jobs_docs.append(job_doc)
    return jobs_docs

  def get_jobs_results(self, user_id: str, job_id: str):
    job_doc = jobs_repository.get_by_query({"user_id": user_id, "job_id": job_id})
    if job_doc == None:
      raise HTTPException(status_code=404)
    results_keys = list(job_doc["results"].keys())
    results_data = {}
    for result_key in results_keys:
      result_id = job_doc["results"][result_key]
      result_doc = results_repository.get(str(result_id))
      if result_doc != None:
        results_data[result_key] = result_doc['data']
    return results_data

  def download_job_result_file(self, user_id: str, job_id: str, result_key: str):
    job_doc = jobs_repository.get_by_query({"user_id": user_id, "job_id": job_id})
    if job_doc == None:
      raise HTTPException(status_code=404)
    try:
      result_id = job_doc["results"][result_key]
      result_doc = results_repository.get(str(result_id))
      if result_doc != None:
        return result_doc['data']
    except KeyError as e:
      raise HTTPException(status_code=404)
    raise HTTPException(status_code=404)


jobs_service = JobsService()
