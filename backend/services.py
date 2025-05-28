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
                INSERT INTO Users (
                    name, email, password_hash, role, address, phone,
                    signup_date, last_login, is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_data["name"],
                    user_data["email"],
                    pwd_hash,
                    "user",
                    user_data["address"],
                    user_data["phone"],
                    datetime.now(),
                    datetime.now(),
                    True
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
        
        # Update last_login time
        now = datetime.now()
        
        cur.execute("SELECT * FROM Users WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            cur.close()
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Update last_login
        cur.execute("UPDATE Users SET last_login = %s WHERE email = %s", (now, email))
        conn.commit()

        payload = {
            "sub": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)
        
        cur.close()
        conn.close()
        
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
            "height_cm": user.get("height_cm"),
            "weight_kg": user.get("weight_kg"),
            "age": user.get("age"),
            "gender": user.get("gender", ""),
            "membershipPlan": user.get("membership_plan", "Free membership"),
            "profile_picture": user.get("profile_picture"),
            "fitness_level": user.get("fitness_level", ""),
            "medical_conditions": user.get("medical_conditions", ""),
            "preferred_training_time": user.get("preferred_training_time", ""),
            "trainer_name": user.get("trainer_name", "Not assigned")
        }

    def update_user_profile(
            self, request: Request, name, email, phone, address,
            height_cm, weight_kg, age, gender, profile_filename,
            fitness_level=None, medical_conditions=None, 
            preferred_training_time=None
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

        # Fetch current user data
        cur.execute("SELECT * FROM Users WHERE email = %s", (current_email,))
        current = cur.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="User not found")

        # Preserve existing profile picture if not updated
        new_picture = profile_filename if profile_filename else current.get("profile_picture")

        # Convert empty strings to None for numeric fields
        height_cm = int(height_cm) if height_cm else current["height_cm"]
        weight_kg = int(weight_kg) if weight_kg else current["weight_kg"]
        age = int(age) if age else current["age"]

        # Use current values if new ones are not provided
        updated_values = {
            "name": name or current["name"],
            "email": email or current["email"],
            "phone": phone or current["phone"],
            "address": address or current["address"],
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "age": age,
            "gender": gender or current["gender"],
            "profile_picture": new_picture,
            "fitness_level": fitness_level or current["fitness_level"],
            "medical_conditions": medical_conditions or current["medical_conditions"],
            "preferred_training_time": preferred_training_time or current["preferred_training_time"]
        }

        cur.execute("""
            UPDATE Users SET
                name=%s, email=%s, phone=%s, address=%s,
                height_cm=%s, weight_kg=%s, age=%s,
                gender=%s, profile_picture=%s,
                fitness_level=%s, medical_conditions=%s,
                preferred_training_time=%s
            WHERE email=%s
        """, (
            updated_values["name"], updated_values["email"],
            updated_values["phone"], updated_values["address"],
            updated_values["height_cm"], updated_values["weight_kg"],
            updated_values["age"], updated_values["gender"],
            updated_values["profile_picture"],
            updated_values["fitness_level"],
            updated_values["medical_conditions"],
            updated_values["preferred_training_time"],
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