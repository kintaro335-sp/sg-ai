import re
import requests
from datetime import datetime

assistant_extractor = "asst_DZ2L5MzY3GtMa7QXzbOGV6As"

base_url_assistant = f"https://brainy-api-sandbox-e4qwagbccq-uc.a.run.app/v1/agents/{assistant_extractor}/completion"

campos = [
    {
        'name': 'nombre de archivo',
        'type': 'text',
        'ai': False,
        'get_from': 'filename'
    },
    {
        'name': 'numero de agente',
        'type': 'text',
        'ai': True,
        'get_from': 'agent_number'
    },
    {
        'name': 'nombre del agente',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'nombre del promotor',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'numero de promotor',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'compañia de seguros',
        'type': 'text',
        'ai': False,
        'get_from': 'insurance'
    },
    {
        'name': 'nombre del contratante',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'nombre de el asegurado',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'poliza',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'descripcion',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'forma de pago',
        'type': 'text',
        'ai': True
    },
    {
        'name': 'fecha de emisión',
        'type': 'date',
        'ai': True
    },
    {
        'name': 'período de cobertura (desde)',
        'type': 'date',
        'ai': True
    },
    {
        'name': 'período de cobertura (hasta)',
        'type': 'date',
        'ai': True
    },
    {
        'name': 'ramo',
        'type': 'text',
        'ai': False,
        'get_from': 'ramo'
    },
    {
        'name': 'prima neta',
        'type': 'number',
        'ai': True
    }
    ]

def get_fields_list_ai(fields:list[dict]):
    fields_list = []
    for field in fields:
        if field['ai']:
            fields_list.append(field['name'])
    return fields_list

def init_dict_data(fields:list[dict]):
    initial_value = ""
    campos =  {}
    for field in fields:
        if field['ai']:
            if field['type'] == 'text':
                initial_value = "No Encontrado"
            else:
                initial_value = ''
            campos[field['name']] = initial_value
    return campos

titular_regex = re.compile(r'[^* <>":|]+[A-Za-z0-9 ]+')

def clear_text(text):
    accepted_text = ''
    accepted_text_arr = titular_regex.findall(text)
    for i in range(len(accepted_text_arr)):
        accepted_text += accepted_text_arr[i]
    return accepted_text

dates_regex = re.compile(r'([0-9]{1,2}\x2F[A-Za-z]+\x2F[0-9]{4}|[0-9]{1,2} de [A-Za-z]+ de [0-9]{4}|[0-9]{1,2}\x2F[0-9]{1,2}\x2F[0-9]{4})')

large_date_regex = re.compile(r'[0-9]{1,2} de [A-Za-z]+ de [0-9]{4}')

short_date_regex = re.compile(r'[0-9]{1,2}\x2F[A-Za-z]+\x2F[0-9]{4}')

short_number_date_regex = re.compile(r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}')

def translate_month(date:str):
  months_l = {
    "Enero": "January",
    "Febrero": "February",
    "Marzo": "March",
    "Abril": "April",
    "Mayo": "May",
    "Junio": "June",
    "Julio": "July",
    "Agosto": "August",
    "septiembre": "September",
    "Octubre": "October",
    "Noviembre": "November",
    "Diciembre": "December"
  }
  months_s = {
    "Ene": "January",
    "Feb": "February",
    "Mar": "March",
    "Abr": "April",
    "May": "May",
    "Jun": "June",
    "Jul": "July",
    "Ago": "August",
    "Sep": "September",
    "Oct": "October",
    "Nov": "November",
    "Dic": "December",
    "ENE": "January",
    "FEB": "February",
    "MAR": "March",
    "ABR": "April",
    "MAY": "May",
    "JUN": "June",
    "JUL": "July",
    "AGO": "August",
    "SEP": "September",
    "OCT": "October",
    "NOV": "November",
    "DIC": "December"
  }
  for key, value in months_l.items():
    if key in date:
      date = date.replace(key, value)
      return date
  for key, value in months_s.items():
    if key in date:
      date = date.replace(key, value)
      return date
  return date


def format_date(date:str):
  date_result = date
  if large_date_regex.search(date):
    print('match large date')
    date_obj = datetime.strptime(translate_month(large_date_regex.search(date).group()), '%d de %B de %Y')
    date_processed = date_obj.strftime('%d/%m/%Y')
    date_result = date_processed
    return date_result
  elif short_date_regex.search(date):
    print('match short date')
    date_obj = datetime.strptime(translate_month(short_date_regex.search(date).group()), '%d/%B/%Y')
    date_processed = date_obj.strftime('%d/%m/%Y')
    date_result = date_processed
    return date_result
  elif short_number_date_regex.search(date):
    print('match short number date')
    date_obj = datetime.strptime(short_number_date_regex.search(date).group(), '%Y-%m-%d')
    date_processed = date_obj.strftime('%m/%d/%Y')
    date_result = date_processed
    return date_result
  return 'not found'
  # return date_result

def limpiar_valor(valor):
    valor = valor.replace('*', '').strip()
    return clear_text(valor)

def convertir_a_numero(valor: str):
    try:
        return float(valor.replace(",", "").replace("$", "").replace(" ", ""))
    except ValueError:
        return None

def process_pdf_text_ai(text: str, thread_id = None):
  body = {
    "model": "gpt-4o",
    "message": text,
    "threadId": thread_id
  }

  if thread_id == None:
    del body['threadId']

  response = requests.post(base_url_assistant, json=body)
  
  if response.status_code != 200:
    return None

  response_json = response.json()

  return response_json

def format_fields_list_ai(text: str):
  global campos
  datos = init_dict_data(campos)

  lineas = text.split('\n')
  
  for linea in lineas:
    for key in list(datos.keys()):
      if key.lower() in linea.lower():
          try:
            datos[key] = limpiar_valor(linea.split(':', 1)[1].strip())
          except IndexError:
            datos[key] = 'No encontrado'
            print('dato no encontrado')

  for field in campos:
    if field['ai']:
      try:
        type = field['type']
        if type == 'text':
          datos[field['name']] = limpiar_valor(datos[field['name']])
        elif type == 'number':
          datos[field['name']] = convertir_a_numero(datos[field['name']])
          if datos[field['name']] == None:
            del datos[field['name']]
        elif type == 'date':
          print('fecha entrada', datos[field['name']])
          datos[field['name']] = format_date(datos[field['name']])
          print('fecha salida', datos[field['name']])
          if datos[field['name']] == 'not found':
            del datos[field['name']]
      except ValueError as valerr:
        print(valerr)
        print('dato no encontrado')
      except KeyError as keyerr:
        print(keyerr)
        print('dato no encontrado')

  return datos