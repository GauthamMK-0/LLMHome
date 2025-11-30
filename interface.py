import requests

LLM_URL = "http://localhost:8000/query"

def send_to_llm(command: str, room: str | None = None):
    try:
        if room:
            full_query = f"(Current room: {room}) {command}"
        else:
            full_query = command

        payload = {"q": full_query}
        res = requests.post(LLM_URL, json=payload, timeout=300)
        res.raise_for_status()
        data = res.json()

        print("\nAssistant:", data.get("response", ""))
        if data.get("action"):
            print("Action:", data["action"])
        if data.get("status"):
            print("Status:", data["status"])

    except Exception as e:
        print(f"Failed to connect to LLM: {e}")


if __name__ == "__main__":
    print("Home Assistant LLM Interface")
    print("Enter the room name and your command below.")
    print("Type 'exit' anytime to quit.\n")

    while True:
        room = input("Room: ").strip()
        if room.lower() in ["exit", "quit", "stop"]:
            print("Goodbye!")
            break

        command = input("Command: ").strip()
        if command.lower() in ["exit", "quit", "stop"]:
            print("Goodbye!")
            break

        if not command:
            print("Please enter a command.\n")
            continue

        send_to_llm(command, room)
