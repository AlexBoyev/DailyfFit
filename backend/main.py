"""
backend/main.py – DailyFit Gym backend
• Public pages: index, about, login, register, chatbot
• Protected pages: dashboard, purchase_program, account_settings
• Nutrition logs
• Membership plan update
• Class registration (current + next week) with per-date capacity
• Personal Trainer assignment
"""
import sys

import populate_database
import os
import requests
from pathlib import Path
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import uvicorn

from fastapi import (
    FastAPI, Request, Form, HTTPException, UploadFile, File,
    status, Path as FPath
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError

from services import UserService, ClassService
from chatbot import get_bot_response
from database import get_connection
from docker_manager import (
    is_docker_running, is_container_running,
    initialize_docker, ensure_schema_loaded
)

# ────────────────────────────────────────────────────────────────────
# 1. ENV / CONFIG
# ────────────────────────────────────────────────────────────────────
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

CAPTCHA_ON = os.getenv("CAPTCHA_ENABLED", "true").lower() == "true"
RECAPTCHA_SK = os.getenv("RECAPTCHA_SECRET_KEY", "")
SITE_KEY = os.getenv("SITE_KEY", "")

# ────────────────────────────────────────────────────────────────────
# 2. Docker-based DB container bootstrap (optional helper)
# ────────────────────────────────────────────────────────────────────
def init_app() -> bool:
    if not is_docker_running():
        print("Docker is not running. Start Docker and try again.")
        return False
    if not is_container_running():
        print("Starting DB container & loading schema …")
        if not initialize_docker() or not ensure_schema_loaded():
            return False
    return True

if not init_app():
    exit(1)

# ────────────────────────────────────────────────────────────────────
# 3. Paths & FastAPI boilerplate
# ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
WEB  = BASE.parent / "frontend"
UPLOAD_DIR = WEB / "images" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(debug=True)
app.mount("/static", StaticFiles(directory=str(WEB)), name="static")
app.mount("/images", StaticFiles(directory=str(WEB / "images")), name="images")
templates = Jinja2Templates(directory=str(WEB))

# ────────────────────────────────────────────────────────────────────
# 4. Helpers
# ────────────────────────────────────────────────────────────────────
def verify_recaptcha(token: str) -> bool:
    if not CAPTCHA_ON:
        return True
    try:
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SK, "response": token},
            timeout=5
        )
        return r.json().get("success", False)
    except:
        return False

def jwt_email(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    except JWTError:
        return None

# ────────────────────────────────────────────────────────────────────
# 5. Public routes
# ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(
        "about.html",
        {"request": request, "is_logged_in": bool(jwt_email(request.cookies.get("token")))}
    )

@app.get("/purchase_program", response_class=HTMLResponse)
def purchase_program(request: Request):
    return templates.TemplateResponse(
        "purchase_program.html",
        {"request": request, "is_logged_in": bool(jwt_email(request.cookies.get("token")))}
    )

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "is_logged_in": bool(jwt_email(request.cookies.get("token")))}
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "site_key": SITE_KEY, "captcha_enabled": CAPTCHA_ON}
    )

@app.get("/personal_trainer", response_class=HTMLResponse)
def personal_trainer(request: Request):
    """
    Display all trainers (loaded from /frontend/images/trainers/) and
    show which one (if any) is currently assigned to the logged-in user.
    """
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    # Build a list of trainers by scanning the directory
    trainers = []
    trainers_dir = WEB / "images" / "trainers"
    if trainers_dir.exists():
        for img_path in trainers_dir.iterdir():
            if img_path.is_file():
                # Derive a display name from the filename (e.g., "john_doe.jpg" → "John Doe")
                name = img_path.stem.replace("_", " ").title()
                img_url = f"/images/trainers/{img_path.name}"
                description = f"{name} is a certified personal trainer."
                trainers.append({
                    "name": name,
                    "img": img_url,
                    "description": description
                })

    # Fetch the currently assigned trainer for this user (using trainer_name column)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT trainer_name FROM Users WHERE email=%s", (email,))
    row = cur.fetchone()
    current_trainer = row[0] if row and row[0] else None
    cur.close()
    conn.close()

    return templates.TemplateResponse(
        "personal_trainer.html",
        {
            "request": request,
            "trainers": trainers,
            "trainer_name": current_trainer
        }
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
    return UserService().register_user(await request.json())

@app.post("/api/chat")
async def chat_api(request: Request):
    msg = (await request.json()).get("message", "")
    return {"reply": get_bot_response(msg)}

# ────────────────────────────────────────────────────────────────────
# 6. Auth middleware
# ────────────────────────────────────────────────────────────────────
PROTECTED = {
    "/dashboard", "/purchase_program",
    "/account_settings", "/class_registration",
    "/update_plan", "/register_class", "/unregister_class",
    "/personal_trainer", "/assign_trainer", "/remove_trainer"
}

@app.middleware("http")
async def auth_guard(request: Request, call_next):
    if request.url.path in PROTECTED:
        if not jwt_email(request.cookies.get("token")):
            return RedirectResponse("/login", 302)
    return await call_next(request)

# ────────────────────────────────────────────────────────────────────
# 7. Dashboard & purchase program
# ────────────────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/purchase_program", response_class=HTMLResponse)
def purchase_program(request: Request):
    return templates.TemplateResponse("purchase_program.html", {"request": request})

# ────────────────────────────────────────────────────────────────────
# 8. Account settings  (nutrition + membership)
# ────────────────────────────────────────────────────────────────────
@app.get("/account_settings", response_class=HTMLResponse)
def account_settings(request: Request):
    # 1. Fetch basic user data (name, email, phone, address, fitness fields, etc.)
    ctx = UserService().get_user_data_from_request(request)
    email = ctx.get("email")

    nutrition_logs = []
    nutrition_pref = None

    if email:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # 2. Find the user’s ID
        cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
        row = cur.fetchone()
        if row:
            uid = row["id"]

            # 3. Load the last 30 nutrition logs
            cur.execute("""
                SELECT id, date, meal_type, calories,
                       protein_grams, carbs_grams, fat_grams, notes
                  FROM NutritionLogs
                 WHERE user_id=%s
              ORDER BY date DESC, created_at DESC
                 LIMIT 30
            """, (uid,))
            nutrition_logs = cur.fetchall()

            # 4. Load the user’s current nutrition preferences
            cur.execute("""
                SELECT type, diet_type
                  FROM NutritionMenus
                 WHERE user_id=%s
              ORDER BY last_updated DESC
                 LIMIT 1
            """, (uid,))
            nutrition_pref = cur.fetchone()

        cur.close()
        conn.close()

    # 5. Inject type & diet_type into the context so Jinja can mark <option selected>
    if nutrition_pref:
        ctx["type"] = nutrition_pref["type"]
        ctx["diet_type"] = nutrition_pref["diet_type"]
    else:
        ctx["type"] = None
        ctx["diet_type"] = None

    # 6. Render template with everything
    return templates.TemplateResponse(
        "account_settings.html",
        {
            "request": request,
            **ctx,
            "nutrition_logs": nutrition_logs
        }
    )

@app.post("/update_nutrition_preferences")
async def update_nutrition_preferences(
        request: Request,
        type: str = Form(...),
        diet_type: str = Form(...)
):
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
    uid = cur.fetchone()[0]

    # Check if user already has nutrition preferences
    cur.execute("SELECT id FROM NutritionMenus WHERE user_id=%s LIMIT 1", (uid,))
    existing = cur.fetchone()

    if existing:
        # Update existing record
        cur.execute("""
            UPDATE NutritionMenus
               SET type = %s,
                   diet_type = %s,
                   last_updated = NOW()
             WHERE user_id = %s
        """, (type, diet_type, uid))
    else:
        # Create new record with default values
        cur.execute("""
            INSERT INTO NutritionMenus (user_id, type, diet_type, title, calories, protein_grams, carbs_grams, fat_grams)
            VALUES (%s, %s, %s, 'Default Plan', 2000, 150, 250, 67)
        """, (uid, type, diet_type))

    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/account_settings?tab=nutrition", 303)

@app.post("/add_nutrition_log")
async def add_nutrition_log(
        request: Request,
        date: str          = Form(...),
        meal_type: str     = Form(...),
        calories: int      = Form(...),
        protein_grams: int = Form(...),
        carbs_grams: int   = Form(...),
        fat_grams: int     = Form(...),
        notes: str         = Form("")
):
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
    uid = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO NutritionLogs
            (user_id, date, meal_type, calories,
             protein_grams, carbs_grams, fat_grams, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (uid, date, meal_type, calories, protein_grams, carbs_grams, fat_grams, notes))
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/account_settings?tab=nutrition", 303)

@app.post("/delete_nutrition_menu")
async def delete_nutrition_menu(request: Request, menu_id: int = Form(...)):
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
    uid = cur.fetchone()[0]

    cur.execute("DELETE FROM NutritionMenus WHERE id=%s AND user_id=%s", (menu_id, uid))
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/account_settings?tab=nutrition", 303)

@app.post("/create_nutrition_menu")
async def create_nutrition_menu(
    request: Request,
    title: str         = Form(...),
    calories: int      = Form(...),
    type: str          = Form(...),
    description: str   = Form(""),
    diet_type: str     = Form(...),
    protein_grams: int = Form(...),
    carbs_grams: int   = Form(...),
    fat_grams: int     = Form(...)
):
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
    uid = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO NutritionMenus (
            user_id, title, calories, type, description, meal_plan,
            diet_type, protein_grams, carbs_grams, fat_grams
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (uid, title, calories, type, description, '{}', diet_type,
          protein_grams, carbs_grams, fat_grams))

    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/account_settings?tab=nutrition", 303)

@app.post("/delete_nutrition_log/{log_id}")
def delete_log(request: Request, log_id: int = FPath(...)):
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE NL FROM NutritionLogs NL
        JOIN Users U ON NL.user_id = U.id
        WHERE NL.id=%s AND U.email=%s
    """, (log_id, email))
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/account_settings?tab=nutrition", 303)

@app.post("/update_plan")
def update_plan(request: Request, plan: str = Form(...)):
    UserService().update_plan(request, plan)
    return RedirectResponse("/account_settings?plan_updated=1", 303)

# ────────────────────────────────────────────────────────────────────
# 9. Class registration (weekly)
# ────────────────────────────────────────────────────────────────────
cls = ClassService()

@app.get("/class_registration", response_class=HTMLResponse)
def class_registration(request: Request):
    rows = cls.upcoming_two_weeks(request)
    return templates.TemplateResponse(
        "class_registration.html",
        {"request": request, "rows": rows, "is_logged_in": True}
    )

@app.post("/register_class/{class_id}")
def register_class(request: Request,
                   class_id: int = FPath(...),
                   date: str = Form(...)):
    uid = cls._user_id(request)
    if not uid:
        return RedirectResponse("/login", 302)
    try:
        cls.register(uid, class_id, date)
    except ValueError:
        pass  # class full
    return RedirectResponse("/class_registration", 303)

@app.post("/unregister_class/{class_id}")
def unregister_class(request: Request,
                     class_id: int = FPath(...),
                     date: str = Form(...)):
    uid = cls._user_id(request)
    if not uid:
        return RedirectResponse("/login", 302)
    cls.cancel(uid, class_id, date)
    return RedirectResponse("/class_registration", 303)

# ────────────────────────────────────────────────────────────────────
# 10. Personal Trainer endpoints
# ────────────────────────────────────────────────────────────────────


@app.post("/assign_trainer")
def assign_trainer(request: Request, trainer_name: str = Form(...)):
    """
    Assigns the given trainer_name to the logged-in user.
    """
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Users SET trainer_name=%s WHERE email=%s",
        (trainer_name, email)
    )
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/personal_trainer", 303)

@app.post("/remove_trainer")
def remove_trainer(request: Request):
    """
    Removes any assigned trainer for the logged-in user.
    """
    email = jwt_email(request.cookies.get("token"))
    if not email:
        return RedirectResponse("/login", 302)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Users SET trainer_name=NULL WHERE email=%s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse("/personal_trainer", 303)

# ────────────────────────────────────────────────────────────────────
# 11. DailyFit Assistant (TinyLLaMA)
# ────────────────────────────────────────────────────────────────────
from tinyllama.llama_api import router as llama_router
app.include_router(llama_router, prefix="/api/llama")

@app.get("/dailyfit_assistant", response_class=HTMLResponse)
def dailyfit_assistant(request: Request):
    return templates.TemplateResponse("dailyfit_assistant.html", {"request": request})

# ────────────────────────────────────────────────────────────────────
# 12. Dev entry-point
# ────────────────────────────────────────────────────────────────────

def check_and_populate():
    """Check user count and populate if needed"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM Users WHERE role="user"')
        count = cur.fetchone()[0]

        if count < 30:
            print(f"⚠️ Only {count} users found. Populating database...")
            populate_database.main()  # Directly call the population function
        else:
            print(f"✅ Found {count} users - database ready")

    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cur.close()
            conn.close()


# Run check before launching app
check_and_populate()

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8001, reload=True)
