from database import get_connection
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import mysql.connector

SECRET = "your-super-secret-key"
security = HTTPBearer()


class TrainingService:
    def get_training_by_goal(self, goal):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM TrainingPlans WHERE goal=%s", (goal,))
        data = cur.fetchall()
        conn.close()
        return data


class NutritionService:
    def get_menu_by_type(self, menu_type):
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM NutritionMenus WHERE type=%s", (menu_type,))
        data = cur.fetchall()
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
                "INSERT INTO Users (name,email,password_hash,role,address,phone) "
                "VALUES(%s,%s,%s,%s,%s,%s)",
                (
                    user_data["name"],
                    user_data["email"],
                    pwd_hash,
                    'user',
                    user_data["address"],
                    user_data["phone"]
                )
            )
            conn.commit()
        except mysql.connector.IntegrityError as e:
            # 1062 = duplicate entry
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
        conn.close()
        if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        payload = {
            "sub": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET, algorithm="HS256")
        return {"token": token, "name": user["name"]}


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        return jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
