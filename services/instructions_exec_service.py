# import os
from pydantic import ValidationError
import time
import variables_env
import copy
import requests
from services.exceptions.instructions.instruction_exec_exception import InstructionError
from openai import OpenAI, APIError
from schemas.body.video_ia.crew_schema import CrewStructureSchema
from general_utils.crew_utils import CrewInstance
from services.instructions_service import instructions_service

base_url_agents = 'https://localhost:8080/v1'


if variables_env.AI_PROVIDER == 'openai':
  client = OpenAI(api_key=variables_env.OPENAI_API_KEY)
elif variables_env.AI_PROVIDER == 'ollama':
  client = OpenAI(base_url=f"{variables_env.OLLAMA_BASE_URL}/v1", api_key="ollama")
else:
  print('AI provider not found')
  exit(1)

class InstructionsExecService:
    
  def execute_prompt(self, system_prompt, transcription, tries = 0):
      try:
        response = client.chat.completions.create(
            model=variables_env.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ]
        )
        content = response.choices[0].message.content
        return content
      except APIError as err:
        max_tries = 5
        if tries < max_tries + 2:
          return self.execute_prompt(system_prompt, transcription, tries+1)
        raise InstructionError(f"Error executing instruction: {err}")

  def generate_title_from_transcription(self, transcription):
    system_prompt = "Genera un título corto, descriptivo y llamativo que resuma claramente el tema principal y el propósito del siguiente contenido. Asegurate de no utilizar caractéres especiales como asteriscos o dos puntos, etc."
    return self.execute_prompt(system_prompt, transcription)

  def execute_prompt_it(self, system_prompt, transcription):
      try:
        response = client.chat.completions.create(
            model=variables_env.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ]
        )
        content = response.choices[0].message.content
        return content
      except APIError as err:
        return self.execute_prompt_it(system_prompt, transcription)

  def execute_chain_instructions(self, instruction: dict, transcription: str):
    result = ''
    steps = []
    system_prompts = instruction['system_prompts']
    for i, item in enumerate(system_prompts):
      section_name = item['section_name']
      prompt = item['prompt']
      if i == 0:
        result = self.execute_prompt(prompt, transcription)
        steps.append({ "section_name": section_name, "result": copy.copy(result) })
      else:
        result = self.execute_prompt(prompt, result)
        steps.append({ "section_name": section_name, "result": copy.copy(result) })
    result_final = ''
    # result_final = result_final + '## PASOS\n\n'
    for step in steps:
      result_final = result_final + str(step['section_name']) + '\n\n' + step['result']
    result_final = result_final + '\n\n## RESULTADO \n\n' + result
    return result_final
    
  def execute_compound_instructions(self, instruction: dict, transcription: str):
    result_final = ''
    system_prompts = instruction['system_prompts']
    for system_prompt in system_prompts:
      section_name = ''
      try:
        section_name = system_prompt['section_name']
      except KeyError:
        print('missing section_name in system_prompt')
      prompt = system_prompt['prompt']
      result = self.execute_prompt(prompt, transcription)
      if section_name != '':
        result_final = result_final + str(section_name) + '\n\n' + result
      else:
        result_final = result_final + result
    return result_final

  def execute_single_instruction(self, instruction: dict, transcription: str):
    system_prompt = instruction['system_prompt']
    result = self.execute_prompt(system_prompt, transcription)
    return result
  
  def execute_crew_instrucrion(self, instruction: dict, transcription: str):
    crew_structure = instruction['crew']
    crew_instance = CrewInstance(CrewStructureSchema(**crew_structure))

    result = crew_instance.kickoff({ 'input': transcription })
    
    return result.raw

  def execute_agent_completions(self, instruction: dict, transcription: str):
    agent = instruction['agent']
    thread_id = None
    try:
      thread_id = instruction['thread_id']
    except KeyError:
      pass
    if thread_id == None:
      thread_id = instructions_service.get_instruction_thread_id_j(instruction['_id'])

    body_json = {
      "model": "gpt-4o",
      "message": transcription,
      "threadId": thread_id
    }

    if thread_id == None:
      del body_json['threadId']

    response = requests.post(f"{base_url_agents}/agents/{agent}/completion", json=body_json)
    
    if response.status_code != 200:
      return f"error getting completion. {response.text.encode('utf8')} status code: {response.status_code}"
    elif response.status_code == 400:
      time.sleep(5)
      return self.execute_agent_completions(instruction, transcription)
    elif response.status_code > 400 and response.status_code < 500:
      raise InstructionError(f"Error executing agent instruction: {response.text.encode('utf8')} status code: {response.status_code}")

    response_json = response.json()

    if thread_id == None:
      instructions_service.update_instruction_thread_id_j(instruction['_id'], response_json['threadId'])

    result = response_json['message']

    return result

  def execute_instruction(self, instruction: dict, transcription: str):
    result = ''
    instruction_type = instruction['type']
    try:
      match instruction_type:
        case 'single':
          result = self.execute_single_instruction(instruction, transcription)
        case 'compound':
          result = self.execute_compound_instructions(instruction, transcription)
        case 'chain':
          result = self.execute_chain_instructions(instruction, transcription)
        case 'crew':
          result = self.execute_crew_instrucrion(instruction, transcription)
        case 'agent':
          result = self.execute_agent_completions(instruction, transcription)
      return result
    except InstructionError as intsruction_error:
      return f"{intsruction_error}"
  
  def execute_instructions(self, instructions: list, transcription: str):
    results = {}
    for instruction in instructions:
      result = self.execute_instruction(instruction, transcription)
      result_obj = dict()
      result_obj['result'] = result
      result_obj['file_prefix'] = instruction['file_prefix']
      results[instruction['name']] = result_obj
    return results

instructions_exec_service = InstructionsExecService()
