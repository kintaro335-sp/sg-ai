import requests


mmonk_base_url = "https://mmonk-8893350593.us-central1.run.app/v1"

def validate_license(license_key: str, license_pin: str):
  if license_key == None or license_pin == None:
    return False
  response = requests.post(f"{mmonk_base_url}/license/validate", json={"license_key": license_key, "pin": license_pin})  

  if response.status_code != 200:
    return False
  else:
    return response.json()['enabled']