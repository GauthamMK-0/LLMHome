import os
import re
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
from datetime import datetime, timedelta

# --- Load environment variables ---
load_dotenv("home.env")

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# --- Initialize FastAPI ---
app = FastAPI(title="Home Assistant LLM", version="2.0")

# --- Load quantized model ---
llm = Llama(
    model_path="models/Qwen2.5-3B-Instruct-Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=6,
    n_batch=128,
    verbose=True
)

# --- Memory Management ---
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    raise ValueError("Empty memory file")
                return json.loads(data)
        except Exception:
            print("[WARN] memory.json corrupted or empty. Resetting memory.")
            return {"events": [], "tasks": []}
    return {"events": [], "tasks": []}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def log_event(description):
    memory = load_memory()
    memory["events"].append({
        "time": datetime.now().isoformat(),
        "event": description
    })
    save_memory(memory)

def add_task(task):
    memory = load_memory()
    memory["tasks"].append({
        "task": task,
        "created": datetime.now().isoformat(),
        "done": False
    })
    save_memory(memory)

def list_tasks():
    memory = load_memory()
    return [t for t in memory["tasks"] if not t.get("done")]

# --- Home Assistant Helper Functions ---
def call_service(domain: str, service: str, entity_id: str):
    """Generic function to call a Home Assistant service."""
    url = f"{HA_URL}/api/services/{domain}/{service}"
    data = {"entity_id": entity_id}
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=5)
        return r.status_code, r.text
    except Exception as e:
        return 500, f"Service call failed: {e}"

def toggle_boolean(entity_id: str):
    """Shortcut for toggling input_booleans."""
    return call_service("input_boolean", "toggle", entity_id)

def fetch_devices():
    """Fetch all entities from Home Assistant."""
    try:
        r = requests.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=5)
        devices = r.json()
        for d in devices:
            d["attributes"] = [f"{k}={v}" for k, v in d.get("attributes", {}).items()]
        return devices
    except Exception as e:
        print(f"[ERROR] Failed to fetch devices: {e}")
        return []

# --- Intent Handler for Memory ---
def handle_memory_intent(user_query):
    query = user_query.lower()

    if query.startswith("remember "):
        note = user_query.replace("remember", "").strip()
        add_task(note)
        return {"response": f"Got it. I’ll remember to {note}.", "action": None}

    if "what did i do yesterday" in query:
        memory = load_memory()
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        events = [e["event"] for e in memory["events"]
                  if e["time"].startswith(yesterday)]
        if events:
            return {"response": "Yesterday you " + ", ".join(events), "action": None}
        else:
            return {"response": "Nothing notable was logged yesterday.", "action": None}

    if "tasks" in query or "to do" in query:
        tasks = list_tasks()
        if not tasks:
            return {"response": "You have no pending tasks right now.", "action": None}
        return {"response": "You still need to: " + ", ".join([t['task'] for t in tasks]), "action": None}

    if "clear memory" in query:
        save_memory({"events": [], "tasks": []})
        return {"response": "All memories have been cleared.", "action": None}

    return None

# --- Data Model ---
class Query(BaseModel):
    q: str

# --- Main Endpoint ---
@app.post("/query")
def handle_query(payload: Query):
    user_query = payload.q.strip()

    # Step 1: Handle special memory intents before LLM
    memory_response = handle_memory_intent(user_query)
    if memory_response:
        log_event(f"User requested memory action: {user_query}")
        return memory_response

    # Step 2: Get devices and context
    devices = fetch_devices()
    now_str = datetime.now().strftime("%I:%M %p on %A %B %d, %Y")

    # Step 3: Load memory and construct context
    memory = load_memory()
    recent_events = memory["events"][-10:]
    pending_tasks = list_tasks()

    history_context = "Recent events:\n" + "\n".join(
        [f"- {e['event']} at {e['time']}" for e in recent_events]
    ) if recent_events else "No recent events recorded."

    tasks_context = "Pending tasks:\n" + "\n".join(
        [f"- {t['task']}" for t in pending_tasks]
    ) if pending_tasks else "No pending tasks."

    # Step 4: Construct LLM system prompt
    system_prompt = f"""
You are 'Al', the local AI assistant that manages home devices and keeps track of what happens in the house.
Current time: {now_str}

{history_context}

{tasks_context}

Tools available: ["toggle_boolean", "call_service"]

Devices:
"""
    # Add device info
    for device in devices:
        area = device.get("area_name", device.get("area_id", "Unknown"))
        system_prompt += f"{device['entity_id']} '{device.get('name','unknown')}' = {device['state']}; area={area}; {';'.join(device['attributes'])}\n"

    system_prompt += f"""
User request: {user_query}

Respond strictly in JSON format:
{{
  "response": "Natural language reply to the user",
  "action": {{
    "domain": "input_boolean" or null,
    "service": "toggle" or null,
    "entity_id": "entity.id" or null
  }}
}}
If no action is needed, set "action": null.
"""

    # Step 5: LLM Inference
    try:
        out = llm(system_prompt, max_tokens=256)
        text = out["choices"][0]["text"].strip()
    except Exception as e:
        return {"response": f"LLM generation failed: {e}", "action": None}

    clean_text = re.sub(r"```(?:json)?", "", text).strip("` \n")

    # Step 6: Parse JSON safely
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError:
        print("[WARN] JSON decode failed. Raw model output:\n", text)
        data = {"response": clean_text, "action": None}

    # Step 7: Execute Action if Any
    action = data.get("action")
    if action and action.get("entity_id"):
        entity_id = action["entity_id"]
        if not entity_id.startswith("input_boolean."):
            entity_id = f"input_boolean.{entity_id}"
            action["entity_id"] = entity_id

        domain = action.get("domain", "input_boolean")
        service = action.get("service", "toggle")

        print(f"[ACTION] Executing {domain}.{service} → {entity_id}")
        status, msg = call_service(domain, service, entity_id)
        data["status"] = f"Action result: {status}, Message: {msg[:200]}"
        log_event(f"Executed {domain}.{service} on {entity_id}")
    else:
        data["status"] = "No action executed"
        log_event(f"User asked: {user_query} — {data.get('response', '')}")

    return data

# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn
    print("Starting LLM Home Assistant (with memory) ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
