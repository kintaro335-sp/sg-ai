import variables_env
from crewai import Agent, Task, Crew, Process, LLM
from schemas.body.video_ia.crew_schema import CrewStructureSchema
from services.exceptions.instructions.instruction_exec_exception import InstructionError
import json


def get_llm():
  if variables_env.AI_PROVIDER == 'openai':
    return LLM(base_url="https://api.openai.com/v1", model=variables_env.AI_MODEL, api_key=variables_env.OPENAI_API_KEY)
  elif variables_env.AI_PROVIDER == 'ollama':
    return LLM(base_url=variables_env.OLLAMA_BASE_URL, model=f"{variables_env.AI_PROVIDER}/{variables_env.AI_MODEL}", api_key="ollama")
  else:
    print('AI provider not found')
    raise InstructionError(f'AI provider not found in .env file: invalid value: {variables_env.AI_MODEL} {variables_env.AI_PROVIDER}')

class CrewInstance:
  def __init__(self, crew_structure: CrewStructureSchema):
    
    crew_structure_json = json.loads(crew_structure.model_dump_json())

    self.process = Process.sequential

    try:
      if crew_structure_json['process'] == 'hierarchical':
        self.process = Process.hierarchical
      elif crew_structure_json['process'] == 'sequential':
        self.process = Process.sequential
    except KeyError:
      self.process = Process.sequential

    # self.inputs = crew_structure_json['inputs']
    self.agents = {}
    self.tasks = {}
    for agent in crew_structure_json['agents']:
      self.agents[agent['name']] = Agent(**agent, llm=get_llm())

    for task in crew_structure_json['tasks']:
      self.tasks[task['name']] = Task(description = task['description'], expected_output = task['expected_output'], agent=self.agents[task['agent']])

    agents_list = []
    for agent in self.agents.values():
      agents_list.append(agent)

    tasks_list = []
    for task in self.tasks.values():
      tasks_list.append(task)

    self.crew = Crew(
      agents=agents_list,
      tasks=tasks_list,
      process=self.process,
      verbose=False,
      cache=False
    )
  
  def kickoff(self, data):
    return self.crew.kickoff(data)


