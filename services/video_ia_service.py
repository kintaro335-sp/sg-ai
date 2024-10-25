import os
import variables_env
import subprocess
from subprocess import CalledProcessError
from fastapi import UploadFile, BackgroundTasks

import math
from openai import OpenAI, APIError
from pathlib import Path

# services

from services.file_manager_service import file_manager_service
from services.jobs_service import jobs_service
from services.projects_service import projects_service
from services.instructions_service import instructions_service
from services.instructions_exec_service import instructions_exec_service
from services.exceptions.jobs.failed_job_exception import FailedJobException
from moviepy.editor import VideoFileClip, AudioFileClip, AudioClip, concatenate_audioclips

from db.mongo.mongo_generic_repository import MongoGenericRepository

client = OpenAI(api_key=variables_env.OPENAI_API_KEY)

class VideoIaService:
  def check_video_codec(self, path: str):
    try:
      codec = subprocess.check_output(
          ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
          '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1',
          str(path)],
          text=True
        ).strip()
      return codec
    except CalledProcessError as cpe:
        raise FailedJobException(f'Error checking video codec {path} \n {cpe.stderr}', 1)

  def convert_to_mp3(self, input_file, output_file):
    try:
      p = subprocess.run([
          'ffmpeg', '-i', str(input_file),
          '-q:a', '0', '-map', 'a',
          str(output_file), '-y'
      ], check=True)
    except CalledProcessError as cpe:
        raise FailedJobException(f'Error converting {input_file} to {output_file} \n {cpe.stderr}', 1)

  def convert_to_h264(self, input_file, output_file):
      try:
        p = subprocess.run([
            'ffmpeg', '-i', str(input_file),
            '-c:v', 'libx264', '-crf', '23',
            '-c:a', 'aac', '-strict', 'experimental',
            str(output_file), '-y'
        ], check=True)
      except CalledProcessError as cpe:
          raise FailedJobException(f'Error converting {input_file} to {output_file} \n {cpe.stderr}', 1)

  def transcribe_with_whisper(self, audio_path):
      if variables_env.OPENAI_API_KEY == None:
        raise FailedJobException('OPENAI_API_KEY is not set', 1)
      try:
          with open(audio_path, "rb") as audio_file:  
              transcript = client.audio.transcriptions.create(
                  model="whisper-1",
                  file=audio_file,
                  language="es"
              )
          return transcript.text
      except Exception as e:  
          print(f"Error al transcribir el archivo: {e}")
          return ""

  def get_audio_segments(self, path: str) -> int:
    max_clip_segment = 10*60
    clip = AudioFileClip(path)
    if clip.duration >= max_clip_segment:
      audio_segmensts = math.ceil(clip.duration / max_clip_segment)
      return audio_segmensts
    return 1

  def transcribe_audio_segments(self, path: Path, path_temp: Path, user_id: str, job_id: str) -> str:
    max_clip_segment = 10*60
    segments = self.get_audio_segments(str(path))
    file_clip = AudioFileClip(filename=str(path))
    content = ''

    if segments == 1:
      content = self.transcribe_with_whisper(path)
      title = instructions_exec_service.generate_title_from_transcription(content)
      jobs_service.update_job_result(user_id, job_id, 'title', { "result": title, "file_prefix": "" })
      return content
  
    path_temp.mkdir(parents=True, exist_ok=True)
    for i in range(0, segments):
      start_segment = max_clip_segment * i
      end_segment = max_clip_segment * (i + 1)
      if end_segment > file_clip.duration:
        end_segment = file_clip.duration
      file_segment_name = f"{path.name}_segment_{i}.ogg"
      file_segment_path = path_temp / file_segment_name
      segment: AudioClip = file_clip.subclip(start_segment, end_segment)
      segment.write_audiofile(file_segment_path, codec="libvorbis")
      content_segment = self.transcribe_with_whisper(file_segment_path)
      if i == 0:
        title = instructions_exec_service.generate_title_from_transcription(content_segment)
        jobs_service.update_job_result(user_id, job_id, 'title', { 'result': title, "file_prefix": "" })
      content  = content + content_segment
      os.remove(file_segment_path)
    # os.remove(path_temp)
    return content

  def process_with_auto_editor(self, input_file, output_file):
      p = subprocess.run(['auto-editor', str(input_file), '--output_file', str(output_file), '--no-open'], check=True)
      if p.returncode != 0:
        raise FailedJobException(f'Error converting {input_file} to {output_file}')


  def process_file(self, job_id: str, user_id: str, project_name: str, file_path: Path):
    try:
      if not file_path.exists():
        raise FailedJobException(f'File not found {str(file_path)}', 1)
      jobs_service.update_job_status(user_id, job_id, 'running')
      jobs_service.update_job_step(user_id, job_id, 'initializing')
      file_suffix = file_path.suffix.lower()

      file_edited_path = file_manager_service.generate_file_edited_path(user_id, project_name, file_path.stem, file_suffix)
      file_h264_path = file_manager_service.generate_file_h264_path(user_id, project_name, file_path.stem)
      file_converted_path = file_manager_service.generate_file_proceced_path(user_id, project_name, file_path.stem)

      audio_segments_path = file_manager_service.generate_audio_segments_path(user_id, project_name, file_path.stem)

      auto_editor = False
      # get project
      project = projects_service.get_project_j(user_id, project_name)
      

      instructions_project = []
      if project != None:
        instructions_project = instructions_service.get_instructions_j(project['instructions'])
        try:
          auto_editor = project['auto_editor']
        except KeyError:
          pass

      if file_suffix in ['.wav', '.opus']:
        jobs_service.update_job_step(user_id, job_id, 'converting')
        # transcribe mp3 file with whisper
        self.convert_to_mp3(file_path, file_converted_path)
        jobs_service.update_job_step(user_id, job_id, 'transcribing')
        transcription = self.transcribe_audio_segments(file_converted_path, audio_segments_path, user_id, job_id)
        jobs_service.update_job_step(user_id, job_id, 'saving')
        jobs_service.update_job_result(user_id, job_id, 'transcription', { "result": transcription, "file_prefix": "" })
        jobs_service.update_job_step(user_id, job_id, 'processing')
        results_transcriptions = instructions_exec_service.execute_instructions(instructions_project, transcription)
        results_transcriptions_keys = results_transcriptions.keys()
        jobs_service.update_job_step(user_id, job_id, 'saving')
        for key in results_transcriptions_keys:
          jobs_service.update_job_result(user_id, job_id, key, results_transcriptions[key])
      elif file_suffix in ['.mp3', '.ogg', '.m4a']:
        jobs_service.update_job_step(user_id, job_id, 'transcribing')
        transcription = self.transcribe_audio_segments(file_path, audio_segments_path, user_id, job_id)
        jobs_service.update_job_step(user_id, job_id, 'saving')
        jobs_service.update_job_result(user_id, job_id, 'transcription', { "result": transcription, "file_prefix": ""})
        jobs_service.update_job_step(user_id, job_id, 'processing')
        results_transcriptions = instructions_exec_service.execute_instructions(instructions_project, transcription)
        results_transcriptions_keys = results_transcriptions.keys()
        jobs_service.update_job_step(user_id, job_id, 'saving')
        for key in results_transcriptions_keys:
          jobs_service.update_job_result(user_id, job_id, key, results_transcriptions[key])
      elif file_suffix in ['.mp4', '.mkv']:
        # TODO: agregar opcion de edicion automatica con auto-editor
        jobs_service.update_job_step(user_id, job_id, 'converting')
        codec = self.check_video_codec(str(file_path))
        if codec == 'h264':
          if auto_editor:
            self.process_with_auto_editor(file_path, file_edited_path)
            jobs_service.update_job_step(user_id, job_id, 'processing')
            self.convert_to_mp3(file_edited_path, file_converted_path)
          else:
            jobs_service.update_job_step(user_id, job_id, 'processing')
            self.convert_to_mp3(file_path, file_converted_path)
        else:
          if auto_editor:
            self.convert_to_h264(file_path, file_h264_path)
            self.process_with_auto_editor(file_h264_path, file_edited_path)
            jobs_service.update_job_step(user_id, job_id, 'processing')
            self.convert_to_mp3(file_edited_path, file_converted_path)
          else:
            jobs_service.update_job_step(user_id, job_id, 'processing')
            self.convert_to_mp3(file_path, file_converted_path)
        jobs_service.update_job_step(user_id, job_id, 'transcribing')
        transcription = self.transcribe_audio_segments(file_converted_path, audio_segments_path, user_id, job_id)
        jobs_service.update_job_step(user_id, job_id, 'saving')
        jobs_service.update_job_result(user_id, job_id, 'transcription', { "result": transcription, "file_prefix": '' })
        jobs_service.update_job_step(user_id, job_id, 'processing')
        results_transcriptions = instructions_exec_service.execute_instructions(instructions_project, transcription)
        results_transcriptions_keys = results_transcriptions.keys()
        jobs_service.update_job_step(user_id, job_id, 'saving')
        for key in results_transcriptions_keys:
          jobs_service.update_job_result(user_id, job_id, key, results_transcriptions[key])
      elif file_suffix in ['.txt', '.md']:
        jobs_service.update_job_step(user_id, job_id, 'processing')
        content = file_path.read_text(encoding='utf-8')
        jobs_service.update_job_result(user_id, job_id, 'transcription', { "result": content, "file_prefix": '' })
        title = instructions_exec_service.generate_title_from_transcription(content)
        jobs_service.update_job_result(user_id, job_id, 'title', { "result" : title, "file_prefix": '' })
        results_transcriptions = instructions_exec_service.execute_instructions(instructions_project, content)
        results_transcriptions_keys = results_transcriptions.keys()
        jobs_service.update_job_step(user_id, job_id, 'saving') 
        for key in results_transcriptions_keys:
          jobs_service.update_job_result(user_id, job_id, key, results_transcriptions[key])
      jobs_service.update_job_status(user_id, job_id, 'success')
      jobs_service.update_job_step(user_id, job_id, 'finished')        
      if file_converted_path.exists():
        os.remove(str(file_converted_path))
      if file_edited_path.exists():
        os.remove(str(file_edited_path))
      if file_h264_path.exists():
        os.remove(str(file_h264_path))
      os.remove(str(file_path))
    # except Exception as e:
    #   print(e)
    #   jobs_service.update_job_status(user_id, job_id, 'failed')
    #   jobs_service.update_job_step(user_id, job_id, 'finished')
    #   jobs_service.update_job_error(user_id, job_id, f"Error processing file: unknown {e}", 0)
    #   os.remove(str(file_path))
    #   if file_converted_path.exists():
    #     os.remove(str(file_converted_path))
    except FailedJobException as job_error:
      jobs_service.update_job_status(user_id, job_id, 'failed')
      jobs_service.update_job_step(user_id, job_id, 'finished')
      jobs_service.update_job_error(user_id, job_id, job_error.reason, job_error.error_code)
      os.remove(str(file_path))
      if file_converted_path.exists():
        os.remove(str(file_converted_path))

  def add_process_task(self, background_tasks: BackgroundTasks, file: UploadFile, user_id: str, project_name: str):

    file_path = file_manager_service.save_file_request(user_id, project_name, 'raw', file)

    job_id = jobs_service.create_job(user_id, file.filename, str(file_path), project_name)

    background_tasks.add_task(self.process_file, job_id, user_id, project_name, file_path)

    return { 'message': 'task started', 'job_id': job_id }

  def initialize_file_state(self, user_id: str, project_name: str, file_name: str, size: int):
    file_manager_service.initialize_file_state(user_id, project_name, 'raw', file_name, size)
    return { 'message': 'file state initialized' }
  
  def write_file_blob(self, user_id: str, project_name: str, file_name: str, position: int, blob: bytes):
    file_manager_service.write_file_blob(user_id, project_name, 'raw', file_name, position, blob)
    return { 'message': 'file blob written' }

  def finish_file(self, user_id: str, project_name: str, file_name: str, background_tasks: BackgroundTasks):
    path_file = file_manager_service.finish_file(user_id, project_name, 'raw', file_name)
    job_id = jobs_service.create_job(user_id, file_name, str(path_file), project_name)
    background_tasks.add_task(self.process_file, job_id, user_id, project_name, path_file)
    return { 'message': 'file finished, Job started', 'job_id': job_id }

video_ia_service = VideoIaService()
