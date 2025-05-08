# backend/main.py

import os
import requests
from pathlib import Path

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from dotenv import load_dotenv

from services import UserService  # uses register_user and login()

# ─── Load .env ───────────────────────────────────────────────────────────────
load_dotenv()
SECRET_KEY           = os.getenv("SECRET_KEY")
ALGORITHM            = os.getenv("ALGORITHM", "HS256")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
SITE_KEY             = os.getenv("SITE_KEY")
CAPTCHA_ENABLED      = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ─── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(debug=True)

# Serve images at /images
app.mount("/images", StaticFiles(directory=str(FRONTEND_DIR / "images")), name="images")
# Jinja2 templates for HTML
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


# ─── Auth middleware ─────────────────────────────────────────────────────────
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    protected = ("/dashboard", "/purchase_program")
    if request.url.path in protected:
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


# ─── reCAPTCHA verification ──────────────────────────────────────────────────
def verify_recaptcha(token: str) -> bool:
    if not CAPTCHA_ENABLED:
        return True
    try:
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET_KEY, "response": token},
            timeout=5
        )
        return r.json().get("success", False)
    except:
        return False


# ─── Public routes ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "site_key": SITE_KEY, "captcha_enabled": CAPTCHA_ENABLED}
    )


@app.post("/login")
async def login_post(request: Request):
    data = await request.json()
    if not verify_recaptcha(data.get("g-recaptcha-response", "")):
        return JSONResponse(status_code=403, content={"detail": "CAPTCHA failed"})
    # UserService.login raises HTTPException on invalid credentials
    result = UserService().login(data["email"], data["password"])
    resp = JSONResponse(content=result)
    resp.set_cookie(
        "token", result["token"],
        httponly=True, samesite="Lax", secure=False, path="/"
    )
    return resp


@app.get("/logout")
def logout(request: Request):
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("token", path="/")
    return resp


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_post(request: Request):
    data = await request.json()
    # Delegate to your service; register_user will raise HTTPException on duplicate
    result = UserService().register_user(data)
    return result  # e.g. {"message": "Registered successfully"}


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


# ─── Protected routes ─────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/purchase_program", response_class=HTMLResponse)
def purchase_program(request: Request):
    return templates.TemplateResponse("purchase_program.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, reload=True)
