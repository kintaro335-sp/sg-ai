import os
import variables_env
from bson import ObjectId
from db.domain.generic_data_respository import DataRepository
from pymongo import MongoClient
from typing import TypeVar, List

T = TypeVar("T")

client = MongoClient(variables_env.MONGO_CONNECTION_STRING)

class MongoGenericRepository(DataRepository[T]):
  def __init__(self, database: str, collection: str):
    self.client = client
    self.db = self.client[database]
    self.collection = self.db[collection]

  def get(self, id: str) -> T:
    return self.collection.find_one({"_id": ObjectId(id)})
    
  def get_by_query(self, query = {}) -> T:
    return self.collection.find_one(query)

  def get_all(self, query = {}, skip=0, limit=20) -> List[T]:
    return list(self.collection.find(query).skip(skip).limit(limit))

  def add(self, entity: T):
    return self.collection.insert_one(entity)

  def add_many(self, entities: List[T]) -> None:
    return self.collection.insert_many(entities)

  def update(self, entity: T):
    return self.collection.update_one({"_id": entity["_id"]}, {"$set": entity}, upsert=True)
  
  def update_by_query(self, query, entity: T):
    return self.collection.update_one(query, {"$set":
        entity}, upsert=True)

  def delete_by_id(self, id: str):
    return self.collection.delete_one({"_id": ObjectId(id)})

  def delete(self, criteria: dict):
    return self.collection.delete_one(criteria)
