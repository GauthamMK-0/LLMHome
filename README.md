# **LLMHome — Local LLM-Powered Home Assistant**

LLMHome is a fully local home-automation system that connects a quantized LLM running via `llama.cpp` to a Home Assistant installation.
It supports natural-language device control, task/memory management, and contextual reasoning using home data.
All inference runs locally using a 3B-parameter model.

---

## **Features**

* Fully local LLM using `llama.cpp`
* Integration with Home Assistant via REST API
* Natural-language device control
* Persistent memory (`memory.json`)
* JSON-based action schema
* Terminal interface for user commands
* Expandable tool set for future automation

---

## **Repository Structure**

```
LLMHome/
│── assistant.py         # Backend LLM + Home Assistant logic (FastAPI server)
│── interface.py         # Terminal interface for sending natural-language queries
│── home.py              # Home Assistant API utilities
│── home.env             # Environment variables (HA URL + Token)
│── requirements.txt     # Python dependencies
│── memory.json          # Persistent event/task memory
│── models/              # GGUF models for llama.cpp
│── venv/                # Python virtual environment (created by user after cloning)
└── README.md
```

---

## **1. Requirements**

### **System Requirements**

* Ubuntu / Linux
* Python 3.10+
* Minimum 8 GB RAM
* Working Home Assistant instance with API access

---

## **2. Create and Activate Virtual Environment**

### Create:

```bash
python3 -m venv venv
```

### Activate:

```bash
source venv/bin/activate
```

---

## **3. Install Dependencies**

Inside the activated venv:

```bash
pip install -r requirements.txt
```

Required packages include:

```
fastapi
uvicorn
llama_cpp_python
requests
python-dotenv
```

---

## **4. Install and Set Up `llama.cpp` for Python**

This project uses **llama.cpp through Python bindings**, provided by the package:

```
llama_cpp_python
```

### **4.1. Install the llama.cpp Python bindings**

The package is already in `requirements.txt`, but you can install manually:

```bash
pip install llama_cpp_python
```

### **4.2. Enable CUDA acceleration (Optional)**

To use CUDA:

```bash
pip install llama_cpp_python[cuda]
```

### **4.3. Confirm installation**

```bash
python3 -c "import llama_cpp; print('llama_cpp working')"
```

If no errors appear, the binding is successfully installed.

### **4.4. How the model is loaded (in `assistant.py`)**

`assistant.py` loads the GGUF model like this:

```python
from llama_cpp import Llama

llm = Llama(
    model_path="models/Qwen2.5-3B-Instruct-Q4_K_M.gguf",
    n_ctx=4096,
    n_threads=6
)
```

You can adjust:

* `n_ctx` → context length
* `n_threads` → number of CPU threads
* `n_gpu_layers` → number of layers offloaded to GPU (if configured)

---

## **5. Home Assistant Setup**

### Create a long-lived access token:

1. Open Home Assistant
2. Navigate to Profile
3. Create a Long-Lived Access Token

### Configure `home.env`:

```
HA_URL=http://homeassistant.local:8123
HA_TOKEN=YOUR_LONG_LIVED_ACCESS_TOKEN
```

---

## **6. Download the LLM Model**

Recommended model:

**Qwen2.5-3B-Instruct-GGUF**

Download:

```bash
hf download Qwen/Qwen2.5-3B-Instruct-GGUF --include "*.gguf" --output-dir models/
```

Ensure the model file is located inside:

```
models/
```

Use any quantization such as `Q4_K_M`.

---

## **7. Running the Backend Server**

Start the backend:

```bash
python3 assistant.py
```

Expected output:

```
Starting LLM Home Assistant...
Uvicorn running on http://0.0.0.0:8000
```

---

## **8. Using the Terminal Interface**

Run:

```bash
python3 interface.py
```

Sample interaction:

```
Room: kitchen
Command: turn on the lights
```

---

## **9. How the System Works**

### Step 1: User Input

The terminal sends the user's natural-language query to the backend.

### Step 2: Memory Handling

Tasks, reminders, and events are stored in `memory.json`.

### Step 3: Context Building

The backend generates a structured prompt containing:

* Device states
* Time and date
* Recent events
* User tasks
* Available Home Assistant actions

### Step 4: LLM Output

The model returns JSON:

```json
{
  "response": "Turning on the kitchen light.",
  "action": {
    "domain": "light",
    "service": "turn_on",
    "entity_id": "light.kitchen"
  }
}
```

### Step 5: Action Execution

Home Assistant REST API is called with the action.

### Step 6: Logging

All actions are saved in `memory.json`.

---

## **10. Example Commands**

**Device Control**

* Turn on the living room lights
* Switch off the bedroom fan

**Tasks**

* Remember to pay the rent
* Show my tasks

**Status**

* What devices are currently on?
* List all kitchen sensors

---

## **11. Future Extensions**

* Voice-to-text interface
* Camera/sensor summarization
* Energy efficiency analytics
* Automatic room context detection
* Custom fine-tuned home LLM

---

