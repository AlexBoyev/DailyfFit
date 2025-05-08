import os
import requests
from pathlib import Path

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from services import UserService
from chatbot import get_bot_response

# ─── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
SECRET_KEY      = os.getenv("SECRET_KEY")
ALGORITHM       = os.getenv("ALGORITHM", "HS256")
CAPTCHA_ENABLED = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"
RECAPTCHA_KEY   = os.getenv("RECAPTCHA_SECRET_KEY")
SITE_KEY        = os.getenv("SITE_KEY")

# ─── Paths & App ───────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI()
# serve everything under /static from your frontend folder (so /static/images/... works)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
# optional: keep /images mount if you still reference /images elsewhere
app.mount("/images", StaticFiles(directory=str(FRONTEND_DIR / "images")), name="images")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))


# ─── Public Pages ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "site_key": SITE_KEY, "captcha_enabled": CAPTCHA_ENABLED}
    )

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


# ─── Auth, CAPTCHA, UserService, etc. (same as before) ─────────────────────────
def verify_recaptcha(token: str) -> bool:
    if not CAPTCHA_ENABLED:
        return True
    try:
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_KEY, "response": token},
            timeout=5
        )
        return r.json().get("success", False)
    except:
        return False


@app.post("/login")
async def login_post(request: Request):
    data = await request.json()
    if not verify_recaptcha(data.get("g-recaptcha-response", "")):
        raise HTTPException(status_code=403, detail="CAPTCHA failed")
    result = UserService().login(data["email"], data["password"])
    resp = JSONResponse(content=result)
    resp.set_cookie("token", result["token"], httponly=True, samesite="Lax", secure=False, path="/")
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("token", path="/")
    return resp

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_post(request: Request):
    data = await request.json()
    return UserService().register_user(data)


# ─── Chatbot API ───────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat_api(request: Request):
    data = await request.json()
    user_msg = data.get("message", "")
    reply   = get_bot_response(user_msg)
    return {"reply": reply}


# ─── Protected Pages ───────────────────────────────────────────────────────────
from jose import jwt, JWTError

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/dashboard", "/purchase_program"):
        token = request.cookies.get("token")
        if not token:
            return RedirectResponse("/login", status_code=302)
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            resp = RedirectResponse("/login", status_code=302)
            resp.delete_cookie("token", path="/")
            return resp
    return await call_next(request)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/purchase_program", response_class=HTMLResponse)
def purchase_program(request: Request):
    return templates.TemplateResponse("purchase_program.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, reload=True)
