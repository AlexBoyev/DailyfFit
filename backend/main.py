import os
import requests
from pathlib import Path

from fastapi import FastAPI, Request, status, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from dotenv import load_dotenv
import uvicorn
from services import UserService
from chatbot import get_bot_response

# ─── Load configuration ───────────────────────────────────────────────────────
load_dotenv()
SECRET_KEY      = os.getenv("SECRET_KEY")
ALGORITHM       = os.getenv("ALGORITHM", "HS256")
CAPTCHA_ENABLED = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"
RECAPTCHA_KEY   = os.getenv("RECAPTCHA_SECRET_KEY")
SITE_KEY        = os.getenv("SITE_KEY")

# ─── Paths & Static mounts ────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
UPLOADS_DIR  = FRONTEND_DIR / "images" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/images", StaticFiles(directory=str(FRONTEND_DIR / "images")), name="images")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# ─── Utility: reCAPTCHA check ─────────────────────────────────────────────────
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

# ─── Public routes ────────────────────────────────────────────────────────────
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

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_post(request: Request):
    data = await request.json()
    return UserService().register_user(data)

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    token = request.cookies.get("token")
    is_logged_in = False
    try:
        if token:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            is_logged_in = True
    except JWTError:
        pass
    return templates.TemplateResponse("about.html", {"request": request, "is_logged_in": is_logged_in})

# ─── Chatbot API ───────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat_api(request: Request):
    data = await request.json()
    reply = get_bot_response(data.get("message", ""))
    return {"reply": reply}

# ─── Auth middleware for protected pages ──────────────────────────────────────
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    protected_paths = ("/dashboard", "/purchase_program", "/account_settings")
    if request.url.path in protected_paths:
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

# ─── Protected routes ─────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/purchase_program", response_class=HTMLResponse)
def purchase_program(request: Request):
    return templates.TemplateResponse("purchase_program.html", {"request": request})

@app.get("/account_settings", response_class=HTMLResponse)
def account_settings(request: Request):
    user_data = UserService().get_user_data_from_request(request)
    nutrition_data = UserService().get_nutrition_data(request)
    return templates.TemplateResponse(
        "account_settings.html", 
        {
            "request": request, 
            **user_data,
            **nutrition_data
        }
    )

@app.post("/update_plan")
async def update_plan(request: Request, plan: str = Form(...)):
    UserService().update_plan(request, plan)
    return RedirectResponse("/account_settings", status_code=303)

@app.post("/update_password")
async def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    template_data = {"request": request}

    if new_password != confirm_password:
        template_data["mismatch_error"] = "Passwords do not match"
        user_data = UserService().get_user_data_from_request(request)
        return templates.TemplateResponse("account_settings.html", {**template_data, **user_data, "active_tab": "securityTab"})

    try:
        UserService().update_password(request, current_password, new_password)
    except HTTPException as e:
        if e.status_code == 403:
            template_data["password_error"] = "Current password is incorrect"
            user_data = UserService().get_user_data_from_request(request)
            return templates.TemplateResponse("account_settings.html", {**template_data, **user_data, "active_tab": "securityTab"})
        else:
            raise

    user_data = UserService().get_user_data_from_request(request)
    return templates.TemplateResponse("account_settings.html", {**template_data, **user_data, "success_message": "Password updated successfully.", "active_tab": "securityTab"})

@app.post("/update_nutrition")
async def update_nutrition(
    request: Request,
    calories: int = Form(None),
    diet_type: str = Form(None),
    protein_grams: int = Form(None),
    carbs_grams: int = Form(None),
    fat_grams: int = Form(None),
    nutrition_notes: str = Form(None)
):
    try:
        UserService().update_nutrition_preferences(
            request,
            calories,
            diet_type,
            protein_grams,
            carbs_grams,
            fat_grams,
            nutrition_notes
        )
        return RedirectResponse(
            "/account_settings?tab=nutritionTab&success=Nutrition preferences updated successfully",
            status_code=303
        )
    except Exception as e:
        template_data = {
            "request": request,
            "nutrition_error": str(e),
            "active_tab": "nutritionTab"
        }
        user_data = UserService().get_user_data_from_request(request)
        nutrition_data = UserService().get_nutrition_data(request)
        return templates.TemplateResponse(
            "account_settings.html", 
            {**template_data, **user_data, **nutrition_data}
        )

@app.post("/account_settings")
async def update_account_settings(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    height_cm: int = Form(None),
    weight_kg: int = Form(None),
    age: int = Form(None),
    gender: str = Form(None),
    profile_picture: UploadFile = File(None),
    existing_profile_picture: str = Form(None)
):
    filename = None

    if profile_picture and profile_picture.filename:
        filename = f"{email}_profile.png"
        file_path = UPLOADS_DIR / filename
        with open(file_path, "wb") as f:
            f.write(await profile_picture.read())
    else:
        filename = existing_profile_picture

    UserService().update_user_profile(
        request, name, email, phone, address,
        height_cm, weight_kg, age, gender, filename
    )
    return RedirectResponse("/account_settings", status_code=303)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, reload=True)