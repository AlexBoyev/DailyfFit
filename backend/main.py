import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from chatbot import get_bot_response

app = FastAPI()

# Run migrations on startup

# Paths
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# Serve images at /images
app.mount("/images", StaticFiles(directory=os.path.join(FRONTEND_DIR, "images")), name="images")
# Serve all other static HTML/CSS/JS in frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

def _serve(file_name: str):
    path = os.path.join(FRONTEND_DIR, file_name)
    return HTMLResponse(open(path, "r", encoding="utf-8").read())

@app.get("/", response_class=HTMLResponse)
async def index():
    return _serve("index.html")

@app.get("/register", response_class=HTMLResponse)
async def register():
    return _serve("register.html")

@app.get("/login", response_class=HTMLResponse)
async def login():
    return _serve("login.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return _serve("dashboard.html")

@app.get("/account_settings", response_class=HTMLResponse)
async def account_settings():
    return _serve("account_settings.html")

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg  = data.get("message", "")
    reply = get_bot_response(msg)
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, reload=True)
