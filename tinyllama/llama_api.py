from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from tinyllama.tinyllama_assistant import get_personalized_llama_reply
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
async def llama_chat(request: Request):
    try:
        data = await request.json()
        user_question = data.get("message", "").strip()

        logger.debug(f"Incoming LLaMA request payload: {data}")

        if not user_question:
            logger.warning("Empty question received")
            return JSONResponse(content={"error": "Message is required."}, status_code=400)

        # Get the assistant's reply and the updated context
        reply, context = get_personalized_llama_reply(request, user_question)
        # Return under the "reply" key so the front-end .reply lookup works
        return {"reply": reply, "context": context}

    except Exception as e:
        logger.exception("Error in llama_chat endpoint")
        return JSONResponse(
            content={"error": f"(TinyLLaMA error) {str(e)}"},
            status_code=500
        )
