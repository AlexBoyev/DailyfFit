# tinyllama/tinyllama_assistant.py

import requests
from backend.services import UserService
from backend.database import get_connection

def get_personalized_llama_reply(request, user_question: str):
    try:
        user_data = UserService().get_user_data_from_request(request)
        email = user_data.get("email")

        if not email:
            return "(TinyLLaMA error) User not authenticated.", "No context returned."

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # ─── 1. PULL THE USER’S BASIC PROFILE (no type/diet_type here) ───
        cur.execute("""
            SELECT
                   id,
                   age,
                   gender,
                   height_cm,
                   weight_kg,
                   medical_conditions,
                   fitness_level,
                   preferred_training_time,
                   trainer_name
              FROM Users
             WHERE email = %s
        """, (email,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return "(TinyLLaMA error) No profile found.", "No context returned."

        user_id = row["id"]

        profile_context = (
            f"Age: {row['age']}, Gender: {row['gender']}, Height: {row['height_cm']} cm, "
            f"Weight: {row['weight_kg']} kg\n"
            f"Medical: {row['medical_conditions'] or 'None'}, "
            f"Fitness Level: {row['fitness_level'] or 'Not specified'}, "
            f"Training Time: {row['preferred_training_time'] or 'Not specified'}, "
            f"Trainer: {row['trainer_name'] or 'None'}"
        )

        # ─── 2. PULL THE 4 MOST RECENT NUTRITION LOGS ───
        cur.execute("""
            SELECT date,
                   meal_type,
                   calories,
                   protein_grams,
                   carbs_grams,
                   fat_grams
              FROM NutritionLogs
             WHERE user_id = %s
          ORDER BY date DESC, created_at DESC
             LIMIT 4
        """, (user_id,))
        meals = cur.fetchall()

        meal_lines = "\n".join([
            f"{m['date']} – {m['meal_type']}: {m['calories']} kcal, "
            f"{m['protein_grams']} g protein, {m['carbs_grams']} g carbs, {m['fat_grams']} g fat"
            for m in meals
        ]) or "No recent meals logged."

        # ─── 3. PULL UPCOMING CLASSES ───
        cur.execute("""
            SELECT cl.name    AS class_name,
                   cr.date    AS class_date
              FROM ClassRegistrations cr
              JOIN Classes cl ON cr.class_id = cl.id
             WHERE cr.user_id = %s 
               AND cr.status = 'registered'
          ORDER BY cr.date DESC
             LIMIT 5
        """, (user_id,))
        classes = cur.fetchall()

        class_lines = "\n".join([
            f"{c['class_date']} – {c['class_name']}"
            for c in classes
        ]) or "No recent class registrations."

        # ─── 4. PULL LATEST NUTRITION MENU (type & diet_type) FROM NutritionMenus ───
        cur.execute("""
            SELECT `type`         AS fitness_goal,
                   diet_type,
                   calories       AS daily_calories,
                   protein_grams,
                   carbs_grams,
                   fat_grams,
                   description
              FROM NutritionMenus
             WHERE user_id = %s
          ORDER BY created_at DESC
             LIMIT 1
        """, (user_id,))
        menu = cur.fetchone()

        if menu:
            fitness_goal     = menu["fitness_goal"]     or "None"
            diet_preference  = menu["diet_type"]        or "None"
            plan_lines = (
                f"Fitness Goals: {fitness_goal}, Diet Type: {diet_preference}\n"
                f"Calories: {menu['daily_calories']} kcal, "
                f"Protein: {menu['protein_grams']} g, "
                f"Carbs: {menu['carbs_grams']} g, "
                f"Fats: {menu['fat_grams']} g\n"
                f"Notes: {menu['description'] or 'None'}"
            )
        else:
            fitness_goal     = "None"
            diet_preference  = "None"
            plan_lines = "No nutrition menu found."

        cur.close()
        conn.close()

        # ─── 5. COMBINE INTO A SINGLE CONTEXT STRING ───
        context = (
            f"{profile_context}\n\n"
            f"Recent meals:\n{meal_lines}\n\n"
            f"Upcoming classes:\n{class_lines}\n\n"
            f"{plan_lines}"
        )

        # ─── 6. BUILD THE LLaMA PROMPT ───
        prompt = f"""
Answer in one short paragraph (maximum 3 sentences). Be direct and practical.
Do not repeat any user information or stats. Adjust your answer to the user's medical condition,
nutrition logs, fitness goals, diet type, and active nutrition menu. take not to what classes the user is registered, 
analyze if its a good fit for him.

User question:
{user_question}
"""

        payload = {
            "model": "gemma3n:latest",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.4
        }

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )

        return response.json().get("response", "(TinyLLaMA error) No response from model."), context

    except Exception as e:
        return f"(TinyLLaMA error) {str(e)}", "No context returned."
