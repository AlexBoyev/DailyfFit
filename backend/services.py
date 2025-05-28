from database import get_connection
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import bcrypt
import mysql.connector
import os

load_dotenv()

# JWT setup
SECRET = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
security = HTTPBearer()


class TrainingService:
    def get_training_by_goal(self, goal):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM TrainingPlans WHERE goal=%s", (goal,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data


class NutritionService:
    def get_menu_by_type(self, menu_type):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM NutritionMenus WHERE type=%s", (menu_type,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data


class UserService:
    def register_user(self, user_data):
        pwd_hash = bcrypt.hashpw(
            user_data["password"].encode(), bcrypt.gensalt()
        ).decode()

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO Users (name, email, password_hash, role, address, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_data["name"],
                    user_data["email"],
                    pwd_hash,
                    "user",
                    user_data["address"],
                    user_data["phone"]
                )
            )
            conn.commit()
        except mysql.connector.IntegrityError as e:
            if e.errno == 1062:
                raise HTTPException(status_code=400, detail="Email already registered.")
            raise
        finally:
            cur.close()
            conn.close()

        return {"message": "Registered successfully"}

    def login(self, email, password):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        payload = {
            "sub": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
        return {
            "token": token,
            "name": user["name"],
            "role": user["role"]
        }

    def get_user_data_from_request(self, request: Request):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "phone": user.get("phone", ""),
            "address": user.get("address", ""),
            "height_cm": user.get("height_cm", ""),
            "weight_kg": user.get("weight_kg", ""),
            "age": user.get("age", ""),
            "gender": user.get("gender", ""),
            "membershipPlan": user.get("membership_plan", "Free membership"),
            "profile_picture": user.get("profile_picture"),
            "fitness_level": user.get("fitness_level", ""),
            "medical_conditions": user.get("medical_conditions", ""),
            "preferred_training_time": user.get("preferred_training_time", ""),
            "trainer_name": user.get("trainer_name", "Not assigned")
        }

    def get_nutrition_data(self, request: Request):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT * FROM NutritionMenus WHERE user_id = (
                SELECT id FROM Users WHERE email = %s
            )
        """, (email,))
        nutrition = cur.fetchone()
        cur.close()
        conn.close()

        if not nutrition:
            return {
                "calories": "",
                "diet_type": "none",
                "protein_grams": "",
                "carbs_grams": "",
                "fat_grams": "",
                "nutrition_notes": ""
            }

        return {
            "calories": nutrition.get("calories", ""),
            "diet_type": nutrition.get("diet_type", "none"),
            "protein_grams": nutrition.get("protein_grams", ""),
            "carbs_grams": nutrition.get("carbs_grams", ""),
            "fat_grams": nutrition.get("fat_grams", ""),
            "nutrition_notes": nutrition.get("description", "")
        }

    def update_user_profile(
            self, request: Request,
            name=None, email=None, phone=None, address=None,
            height_cm=None, weight_kg=None, age=None, gender=None,
            profile_filename=None, fitness_level=None,
            medical_conditions=None, preferred_training_time=None
    ):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            current_email = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM Users WHERE email = %s", (current_email,))
        current = cur.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="User not found")

        updated = {
            "name": name or current["name"],
            "email": email or current["email"],
            "phone": phone or current["phone"],
            "address": address or current["address"],
            "height_cm": height_cm if height_cm is not None else current["height_cm"],
            "weight_kg": weight_kg if weight_kg is not None else current["weight_kg"],
            "age": age if age is not None else current["age"],
            "gender": gender or current["gender"],
            "profile_picture": profile_filename or current["profile_picture"],
            "fitness_level": fitness_level or current["fitness_level"],
            "medical_conditions": medical_conditions or current["medical_conditions"],
            "preferred_training_time": preferred_training_time or current["preferred_training_time"]
        }

        cur.execute("""
            UPDATE Users SET
                name=%s, email=%s, phone=%s, address=%s,
                height_cm=%s, weight_kg=%s, age=%s, gender=%s,
                profile_picture=%s, fitness_level=%s, medical_conditions=%s,
                preferred_training_time=%s
            WHERE email=%s
        """, (
            updated["name"], updated["email"], updated["phone"], updated["address"],
            updated["height_cm"], updated["weight_kg"], updated["age"], updated["gender"],
            updated["profile_picture"], updated["fitness_level"],
            updated["medical_conditions"], updated["preferred_training_time"],
            current_email
        ))

        conn.commit()
        cur.close()
        conn.close()

    def update_plan(self, request: Request, plan: str):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        email = payload.get("sub")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET membership_plan=%s WHERE email=%s", (plan, email))
        conn.commit()
        cur.close()
        conn.close()

    def update_password(self, request: Request, current_password: str, new_password: str):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Get current user
        cur.execute("SELECT * FROM Users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user or not bcrypt.checkpw(current_password.encode(), user["password_hash"].encode()):
            raise HTTPException(status_code=403, detail="Current password incorrect")

        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        cur.execute("UPDATE Users SET password_hash=%s WHERE email=%s", (new_hash, email))
        conn.commit()
        cur.close()
        conn.close()

    def update_nutrition_preferences(
            self, request: Request, calories, diet_type,
            protein_grams, carbs_grams, fat_grams, nutrition_notes
    ):
        token = request.cookies.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        conn = get_connection()
        cur = conn.cursor()

        try:
            # First, check if a nutrition menu exists for this user
            cur.execute("""
                SELECT id FROM NutritionMenus WHERE user_id = (
                    SELECT id FROM Users WHERE email = %s
                )
            """, (email,))

            result = cur.fetchone()

            if result:
                # Update existing menu
                cur.execute("""
                    UPDATE NutritionMenus 
                    SET calories = %s, diet_type = %s,
                        protein_grams = %s, carbs_grams = %s,
                        fat_grams = %s, description = %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = (SELECT id FROM Users WHERE email = %s)
                """, (calories, diet_type, protein_grams, carbs_grams, fat_grams, nutrition_notes, email))
            else:
                # Create new menu
                cur.execute("""
                    INSERT INTO NutritionMenus (
                        user_id, calories, diet_type, protein_grams,
                        carbs_grams, fat_grams, description, type
                    )
                    SELECT id, %s, %s, %s, %s, %s, %s, 'fitness'
                    FROM Users WHERE email = %s
                """, (calories, diet_type, protein_grams, carbs_grams, fat_grams, nutrition_notes, email))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cur.close()
            conn.close()


def get_current_user(
        creds: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        return jwt.decode(creds.credentials, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")