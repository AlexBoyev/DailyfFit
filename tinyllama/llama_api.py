# tinyllama/tinyllama_api.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from tinyllama.tinyllama_assistant import get_personalized_llama_reply

router = APIRouter()


@router.post("/api/llama")
async def llama_chat(request: Request):
    try:
        data = await request.json()
        user_question = data.get("message", "").strip()

        if not user_question:
            return JSONResponse(content={"error": "Message is required."}, status_code=400)

        reply, context = get_personalized_llama_reply(request, user_question)
        return {"reply": reply, "context": context}

    except Exception as e:
        return JSONResponse(
            content={"error": f"(TinyLLaMA error) {str(e)}"},
            status_code=500
        )

