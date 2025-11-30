import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path = "home.env")

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

try:
  response = requests.get(f"{HA_URL}/api/states", headers=headers)
  if response.status_code ==200:
    print("success")

  else:
    print("failed")

except requests.exceptions.RequestException as e:
  print("Error")


def call_service(domain, service, entity_id):
    url = f"{HA_URL}/api/services/{domain}/{service}"
    data = {"entity_id": entity_id}
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=5)
        return r.status_code, r.text
    except Exception as e:
        return 500, str(e)

def toggle_boolean(entity_id):
    # Toggle input_boolean to simulate lights/fans
    domain = "input_boolean"
    service = "toggle"
    return call_service(domain, service, entity_id)
