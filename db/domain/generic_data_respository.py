from typing import TypeVar, Generic, List
from abc import ABC, abstractmethod

T = TypeVar("T")


# Generic repository for MySQL, MongoDB, XML (get, get_all, add, update, delete)
class DataRepository(Generic[T], ABC):
  @abstractmethod
  def get(self, id: int) -> T:
    pass

  @abstractmethod
  def get_all(self) -> List[T]:
    pass

  @abstractmethod
  def add(self, entity: T) -> None:
    pass

  @abstractmethod
  def add_many(self, entities: List[T]) -> None:
    pass

  @abstractmethod
  def update(self, entity: T) -> None:
    pass

  @abstractmethod
  def delete(self, id: int) -> None:
    pass
