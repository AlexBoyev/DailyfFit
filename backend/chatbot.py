# backend/chatbot.py
import json
import random
import re
from pathlib import Path

# Load once on import
_intents_path = Path(__file__).parent / "intents.json"
_intents_data = json.loads(_intents_path.read_text(encoding="utf-8"))
_intents = _intents_data.get("intents", [])


def get_bot_response(user_msg: str) -> str:
    msg = user_msg.lower().strip()
    # Try each intent
    for intent in _intents:
        for pattern in intent["patterns"]:
            # simple word-boundary match
            if re.search(r"\b" + re.escape(pattern.lower()) + r"\b", msg):
                return random.choice(intent["responses"])
    # fallback
    return "Sorry, I didn't quite get that. Could you rephrase?"
