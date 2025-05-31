"""
backend/services.py
UserService  ·  ClassService (weekly booking)
"""

from __future__ import annotations
import os
from datetime import date, timedelta, datetime
from typing import Dict, Any, List, Optional

from fastapi import Request, HTTPException
from jose import jwt, JWTError
from passlib.hash import bcrypt
from database import get_connection

# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

# -------------------------------------------------------------------
#  USER SERVICE  (only methods referenced by main.py)
# -------------------------------------------------------------------
class UserService:

    @staticmethod
    def _hash(pw: str) -> str: return bcrypt.hash(pw)

    # ----- basic queries -------------------------------------------
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE email=%s", (email,))
        user = cur.fetchone(); cur.close(); conn.close()
        return user

    # ----- login ----------------------------------------------------
    def login(self, email: str, password: str) -> Dict[str, str]:
        user = self.get_user_by_email(email)
        if not user or not bcrypt.verify(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = jwt.encode({"sub": email}, SECRET_KEY, algorithm=ALGORITHM)
        return {"token": token, "name": user["name"]}

    # ----- registration --------------------------------------------
    def register_user(self, data: Dict[str, str]):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO Users (name,email,password_hash,phone,address)
            VALUES (%s,%s,%s,%s,%s)
        """, (data["name"], data["email"], self._hash(data["password"]),
              data.get("phone",""), data.get("address","")))
        conn.commit(); cur.close(); conn.close()
        return {"status": "registered"}

    # ----- ctx dict for templates ----------------------------------
    def get_user_data_from_request(self, request: Request) -> Dict[str, Any]:
        email = jwt.decode(request.cookies.get("token"), SECRET_KEY,
                           algorithms=[ALGORITHM])["sub"]
        return self.get_user_by_email(email) or {}

    # ----- membership + password updates ---------------------------
    def update_plan(self, request: Request, plan: str):
        email = jwt.decode(request.cookies.get("token"), SECRET_KEY,
                           algorithms=[ALGORITHM])["sub"]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("UPDATE Users SET membership_plan=%s WHERE email=%s",
                    (plan, email))
        conn.commit(); cur.close(); conn.close()

    def update_password(self, request: Request,
                        current_pw: str, new_pw: str):
        email = jwt.decode(request.cookies.get("token"), SECRET_KEY,
                           algorithms=[ALGORITHM])["sub"]
        user  = self.get_user_by_email(email)
        if not bcrypt.verify(current_pw, user["password_hash"]):
            raise HTTPException(status_code=403, detail="wrong-password")
        conn = get_connection(); cur = conn.cursor()
        cur.execute("UPDATE Users SET password_hash=%s WHERE email=%s",
                    (self._hash(new_pw), email))
        conn.commit(); cur.close(); conn.close()

    def update_user_profile(
            self, request: Request,
            name: str | None, email: str | None, phone: str | None, address: str | None,
            height_cm: int | None, weight_kg: int | None, age: int | None, gender: str | None,
            profile_picture: str | None,
            fitness_level: str | None, medical_conditions: str | None,
            preferred_training_time: str | None
    ):
        """
        Updates Users table. Any arg that is None is ignored (keeps current value).
        Called by /account_settings route for both basic-profile and fitness forms.
        """
        # who is the user
        token = request.cookies.get("token")
        cur_email = jwt.decode(token, SECRET_KEY,
                               algorithms=[ALGORITHM])["sub"]

        # gather only the provided fields
        cols, vals = [], []
        mapping = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "age": age,
            "gender": gender,
            "profile_picture": profile_picture,
            "fitness_level": fitness_level,
            "medical_conditions": medical_conditions,
            "preferred_training_time": preferred_training_time
        }
        for col, val in mapping.items():
            if val is not None and val != "":
                cols.append(f"{col}=%s")
                vals.append(val)

        if not cols:  # nothing to change
            return

        vals.append(cur_email)  # WHERE email = ?

        # run the update
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"UPDATE Users SET {', '.join(cols)} WHERE email=%s", vals)
        conn.commit()
        cur.close()
        conn.close()

# -------------------------------------------------------------------
#  CLASS SERVICE  – supports weekly booking
# -------------------------------------------------------------------
class ClassService:

    # ----- helper: map request → user_id ---------------------------
    def _user_id(self, request: Request) -> Optional[int]:
        token = request.cookies.get("token")
        if not token:
            return None
        try:
            email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
        except JWTError:
            return None
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id FROM Users WHERE email=%s", (email,))
        row = cur.fetchone(); cur.close(); conn.close()
        return row[0] if row else None

    # ----- list current & next week --------------------------------
    def upcoming_two_weeks(self, request: Request) -> List[Dict[str, Any]]:
        uid       = self._user_id(request)
        today     = date.today()
        this_monday = today - timedelta(days=today.weekday())
        next_monday = this_monday + timedelta(days=7)

        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id,name,instructor,capacity,difficulty,
                   schedule_day,schedule_time
              FROM Classes
             WHERE is_active = 1
        """)
        class_rows = cur.fetchall()
        cur.close(); conn.close()

        day_idx = {"monday":0,"tuesday":1,"wednesday":2,
                   "thursday":3,"friday":4,"saturday":5,"sunday":6}

        rows: List[Dict[str,Any]] = []
        for base in (this_monday, next_monday):
            for c in class_rows:
                cdate = base + timedelta(days=day_idx[c["schedule_day"]])

                # capacity + user-flag for that date
                conn = get_connection(); cur = conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM ClassRegistrations
                     WHERE class_id=%s AND date=%s AND status='registered'
                """, (c["id"], cdate))
                taken = cur.fetchone()[0]

                cur.execute("""
                    SELECT 1 FROM ClassRegistrations
                     WHERE user_id=%s AND class_id=%s AND date=%s
                       AND status='registered'
                """, (uid, c["id"], cdate))
                is_reg = cur.fetchone() is not None
                cur.close(); conn.close()

                td = c["schedule_time"]; mins = td.seconds//60
                rows.append({
                    "class_id":      c["id"],
                    "name":          c["name"],
                    "instructor":    c["instructor"],
                    "difficulty":    c["difficulty"],
                    "capacity":      c["capacity"],
                    "spots_left":    c["capacity"]-taken,
                    "time":          f"{mins//60:02d}:{mins%60:02d}",
                    "weekday":       c["schedule_day"].capitalize(),
                    "schedule_date": cdate.isoformat(),
                    "is_registered": is_reg,
                })

        return sorted(rows, key=lambda r: (r["schedule_date"], r["time"]))

    # alias for backward compat
    list_with_status = upcoming_two_weeks
    get_active_classes_with_user_flag = upcoming_two_weeks

    # ----- register ------------------------------------------------
    def register(self, user_id: int, class_id: int, date_iso: str):
        cdate = datetime.fromisoformat(date_iso).date()
        conn = get_connection(); cur = conn.cursor()

        # capacity guard
        cur.execute("""
            SELECT capacity - (
                SELECT COUNT(*) FROM ClassRegistrations
                 WHERE class_id=%s AND date=%s AND status='registered')
            FROM Classes WHERE id=%s
        """, (class_id, cdate, class_id))
        if cur.fetchone()[0] <= 0:
            cur.close(); conn.close()
            raise ValueError("Class full")

        # ensure single row for that (user,class,date)
        cur.execute("""
            DELETE FROM ClassRegistrations
             WHERE user_id=%s AND class_id=%s AND date=%s
        """, (user_id, class_id, cdate))

        cur.execute("""
            INSERT INTO ClassRegistrations
                (user_id,class_id,date,status)
            VALUES (%s,%s,%s,'registered')
        """, (user_id, class_id, cdate))
        conn.commit(); cur.close(); conn.close()

    # ----- cancel --------------------------------------------------
    def cancel(self, user_id: int, class_id: int, date_iso: str):
        cdate = datetime.fromisoformat(date_iso).date()
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""
            UPDATE ClassRegistrations
               SET status='cancelled'
             WHERE user_id=%s AND class_id=%s AND date=%s
               AND status='registered'
        """, (user_id, class_id, cdate))
        conn.commit(); cur.close(); conn.close()
