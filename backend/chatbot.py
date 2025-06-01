# backend/chatbot.py
import json
import random
import re
from pathlib import Path
import requests

# Load once on import
_intents_path = Path(__file__).parent / "intents.json"
_intents_data = json.loads(_intents_path.read_text(encoding="utf-8"))
_intents = _intents_data.get("intents", [])


def get_bot_response(user_msg: str) -> str:
    msg = user_msg.lower().strip()

    # Try each intent (rules-based)
    for intent in _intents:
        for pattern in intent["patterns"]:
            if re.search(r"\b" + re.escape(pattern.lower()) + r"\b", msg):
                return random.choice(intent["responses"])

    # Fallback to TinyLLaMA via Ollama
    try:
        response = requests.post("http://localhost:11434/api/chat", json={
            "model": "tinyllama",
            "messages": [{"role": "user", "content": user_msg}]
        }, timeout=30)
        return response.json()["message"]["content"]
    except Exception as e:
        return f"(TinyLLaMA offline) Sorry, I didn't understand that. Error: {str(e)}"
