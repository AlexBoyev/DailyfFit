# tinyllama/tinyllama_assistant.py
import requests
import logging
from fastapi import Request
from backend.services import UserService
from backend.database import get_connection

logger = logging.getLogger(__name__)


def get_personalized_llama_reply(request: Request, user_question: str):
    """
    Builds the prompt from user context, sends it to a TinyLLaMA inference server,
    and returns the generated reply along with updated context.
    """
    # --- Build user context from your database/services ---
    try:
        # Example: fetch user ID from cookie/token in request
        token = request.cookies.get("token")
        email = None
        if token:
            # Replace this with your real JWT parsing logic
            from jose import jwt, JWTError
            try:
                payload = jwt.decode(token, "your_jwt_secret", algorithms=["HS256"])
                email = payload.get("sub")
            except JWTError:
                email = None

        user_data = None
        if email:
            svc = UserService(get_connection())
            user_data = svc.get_user_by_email(email)

        # Fallback defaults
        age = user_data.age if user_data else None
        gender = user_data.gender if user_data else None
        height = user_data.height_cm if user_data else None
        weight = user_data.weight_kg if user_data else None
        fitness_level = user_data.fitness_level if user_data else None
        medical_conditions = user_data.medical_conditions if user_data else None
        membership = user_data.membership_plan if user_data else None

        # Construct prompt
        context = (f"Age: {age}, Gender: {gender}, "
                   f"Height: {height} cm, Weight: {weight} kg\n"
                   f"Medical: {medical_conditions}, Fitness Level: {fitness_level}, "
                   f"Plan: {membership}\n\n"
                   f"User asks: {user_question}\n"
                   f"Assistant:" )

        payload = {
            "prompt": context,
            "stream": False,
            "temperature": 0.4
        }

        # Call TinyLLaMA inference server
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        result = resp.json()
        logger.debug("⟵ TinyLLaMA raw response: %s", result)

        # Extract text from known fields
        if "response" in result:
            text = result["response"]
        elif "generated_text" in result:
            text = result["generated_text"]
        elif isinstance(result.get("results"), list) and result["results"]:
            text = result["results"][0].get("text", "")
        else:
            text = str(result)

        # Ensure non-empty
        reply = text.strip() if isinstance(text, str) and text.strip() else "(TinyLLaMA error) No text field found."
        return reply, context

    except Exception as e:
        logger.exception("Error calling TinyLLaMA server")
        return f"(TinyLLaMA error) {e}", ""
