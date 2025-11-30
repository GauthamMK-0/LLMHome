# **LLMHome — Local LLM-Powered Home Assistant**

LLMHome is a fully local home-automation system that connects a quantized LLM running via `llama.cpp` to a Home Assistant installation.
It supports natural-language control, device automation, task/memory management, and contextual reasoning using home data.

This project works offline and performs all inference locally using a 3B-parameter LLM.

---

## **Features**

* Fully local LLM using `llama.cpp`
* Integrates with Home Assistant via REST API
* Natural-language device control (lights, fans, switches, sensors)
* Persistent task and event memory (`memory.json`)
* Context-aware responses with recent history and pending tasks
* JSON-based action interface
* Simple terminal interface (`interface.py`)
* Expandable tool set for future automation

---

## **Repository Structure**

```
LLMHome/
│── assistant.py       # Backend server running the LLM and Home Assistant logic
│── interface.py       # Terminal-based user interface for sending commands
│── home.py            # Basic Home Assistant API access and validation
│── home.env           # Environment variables (HA URL and token)
│── models/            # GGUF quantized models for llama.cpp
│── memory.json        # Persistent memory storage
└── README.md
```

---

## **1. Requirements**

### **System Requirements**

* Ubuntu / Linux recommended
* Python 3.10+
* 8 GB RAM minimum (for 3B model)
* Working Home Assistant installation with API access

### **Python Packages**

Install dependencies:

```bash
pip install -r requirements.txt
```

Typical dependencies include:

* `fastapi`
* `uvicorn`
* `llama_cpp_python`
* `requests`
* `python-dotenv`

---

## **2. Home Assistant Setup**

### **Create Long-Lived Access Token**

1. Open Home Assistant
2. Profile → Long-lived access tokens
3. Generate token

### **Configure `home.env`**

Create a file named `home.env`:

```
HA_URL=http://homeassistant.local:8123
HA_TOKEN=YOUR_LONG_LIVED_TOKEN
```

---

## **3. Download the LLM Model**

Example (Qwen2.5-3B):

```bash
hf download Qwen/Qwen2.5-3B-Instruct-GGUF --include "*.gguf" --output-dir models/
```

Use any `Q4_K_M` or similar quantized GGUF file.

Place the downloaded file inside:

```
models/Qwen2.5-3B-Instruct-Q4_K_M.gguf
```

---

## **4. Running the LLM Backend**

Start the backend server:

```bash
python3 assistant.py
```

You should see:

```
Starting LLM Home Assistant...
Uvicorn running on http://0.0.0.0:8000
```

The backend:

* Loads the LLM
* Loads device states from Home Assistant
* Reads memory
* Waits for natural language queries via `/query`

---

## **5. Using the Terminal Interface**

Run:

```bash
python3 interface.py
```

The interface will ask for:

```
Room:
Command:
```

Example:

```
Room: living_room
Command: turn on the lights
```

The backend responds with:

* A natural-language answer
* A structured JSON action
* Execution result/status

---

## **6. How the System Works**

### **1. Input**

User enters a natural-language query via the terminal interface.
Example:

```
"Turn on the bedroom fan"
```

### **2. Memory and Task Handling**

Before calling the LLM:

* Checks if the query is a memory instruction
* Supports:

  * "remember ..."
  * "what did I do yesterday?"
  * "show my tasks"
  * "clear memory"

### **3. Context Construction**

The backend creates a system prompt containing:

* Current time
* Recent events
* Pending tasks
* All Home Assistant devices, states, and attributes
* Available tools (`toggle_boolean`, `call_service`)

### **4. LLM Output**

The model must respond in JSON:

```json
{
  "response": "...",
  "action": {
    "domain": "input_boolean",
    "service": "toggle",
    "entity_id": "input_boolean.living_room_light"
  }
}
```

### **5. Action Execution**

If `action` is non-null:

* Performs a Home Assistant service call
* Logs the event
* Returns execution status

### **6. Memory Logging**

All events and actions are stored in `memory.json`:

```
{
  "events": [...],
  "tasks": [...]
}
```

---

## **7. Example Commands**

### **Device Control**

* "Turn off the kitchen light"
* "Toggle the living room fan"
* "Switch on the bedroom AC"

### **Task Management**

* "Remember to pay the electricity bill"
* "What tasks do I still have?"
* "Clear memory"

### **Home Status Queries**

* "What devices are currently on?"
* "Show me all entities in the kitchen"

---


## **8. Future Extensions**

* Add voice interface
* Add multi-room automatic context
* Add camera and sensor summarization
* Automate energy reporting
* Add fine-tuned home-specific LLM

---


