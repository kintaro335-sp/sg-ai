import os
from typing import Literal, Dict

from fastapi import HTTPException

from pathlib import Path

from fastapi import UploadFile

data_dir = f'{os.getcwd()}/data'

class FileState:
  def __init__(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str, size: int) -> None:
    self.path = Path(f'{data_dir}/{user_id}/{project_name}/{file_type}/{file_name}')
    self.size = size
    self.writen = 0
    self.sectors_written = []
  
  def exist_file(self) -> bool:
    return self.path.exists()

  def write(self, position: int, size: int):
    self.writen += size
    self.sectors_written.append([position, position + size])

  def is_complete(self) -> bool:
    return self.writen == self.size

class FileManagerService:

  def __init__(self):
    self.fileStates: Dict[str, FileState] = {}

  def __exist_file_state(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str):
    try:
      return self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}'] != None
    except KeyError:
      return False

  def get_file_state(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str):
    try:
      return self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}']
    except KeyError:
      return None

  def initialize_file_state(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str, size: int):
    file_path = Path(f'{data_dir}/{user_id}/{project_name}/{file_type}/{file_name}')

    if file_path.exists():
      raise HTTPException(status_code=409, detail="File already exists")
    
    self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}'] = FileState(user_id, project_name, file_type, file_name, size)
    dir_path = Path(f'{data_dir}/{user_id}/{project_name}/{file_type}')
    dir_path.mkdir(parents=True, exist_ok=True)

    with open(f'{data_dir}/{user_id}/{project_name}/{file_type}/{file_name}', 'wb') as buffer:
      buffer.write(b'\0' * size)

  def write_file_blob(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str, position: int, blob: bytes):
    exist_file_state = self.__exist_file_state(user_id, project_name, file_type, file_name)
    if not exist_file_state:
      raise HTTPException(status_code=404, detail="File not found")
      return False
    exist_file = self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}'].exist_file()
    mode_w = 'r+b'
    if not exist_file:
      mode_w = 'wb'
    with open(f'{data_dir}/{user_id}/{project_name}/{file_type}/{file_name}', mode=mode_w) as buffer:
      buffer.seek(position)
      buffer.write(blob)
    self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}'].write(position, len(blob))
    return True

  def finish_file(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str):
    try:
      del self.fileStates[f'{user_id}_{project_name}_{file_type}_{file_name}']
    except KeyError:
      pass
    return Path(f'{data_dir}/{user_id}/{project_name}/{file_type}/{file_name}')

  def save_file_request(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file: UploadFile, overwrite: bool = True):
    file_dir = f'{data_dir}/{user_id}/{project_name}/{file_type}'
    Path(file_dir).mkdir(parents=True, exist_ok=True)
    file_path = f'{file_dir}/{file.filename}'
    file_path_obj = Path(file_path)
    if file_path_obj.exists() and not overwrite and not self.__exist_file_state(user_id, project_name, file_type, file.filename):
      raise HTTPException(status_code=400, detail="File already exists")
    with open(file_path, "wb") as buffer:
      buffer.write(file.file.read())
    return file_path_obj

  def read_file(self, path_file: Path):
    with open(path_file, 'r') as buffer:
      return buffer.read()

  def get_files(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"]):
    file_dir = f'{data_dir}/{user_id}/{project_name}/{file_type}'
    return os.listdir(file_dir)

  def delete_file(self, user_id: str, project_name: str, file_type: Literal["raw", "processed"], file_name: str):
    file_dir = f'{data_dir}/{user_id}/{project_name}/{file_type}'
    file_path = f'{file_dir}/{file_name}'
    os.remove(file_path)

  def generate_file_edited_path(self, user_id: str, project_name: str, file_name_stem: str, file_suffix: str):
    directory = f'{data_dir}/{user_id}/{project_name}/edited'
    Path(directory).mkdir(parents=True, exist_ok=True)
    return Path(f'{directory}/{file_name_stem}{file_suffix}')

  def generate_file_h264_path(self, user_id: str, project_name: str, file_name_stem: str):
    directory = f'{data_dir}/{user_id}/{project_name}'
    Path(directory).mkdir(parents=True, exist_ok=True)
    return Path(f'{directory}/{file_name_stem}_h264.mp4')

  def generate_file_proceced_path(self, user_id: str, project_name: str, file_name_stem: str):
    directory = f'{data_dir}/{user_id}/{project_name}/processed'
    Path(directory).mkdir(parents=True, exist_ok=True)
    return Path(f'{directory}/{file_name_stem}.mp3')

  def generate_audio_segments_path(self, user_id: str, project_name: str, file_name_stem: str):
    return Path(f'{data_dir}/{user_id}/{project_name}/audio_segments/{file_name_stem}')



file_manager_service = FileManagerService()
