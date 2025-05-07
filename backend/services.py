from database import get_connection
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
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


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        return jwt.decode(creds.credentials, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

load_dotenv()

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")