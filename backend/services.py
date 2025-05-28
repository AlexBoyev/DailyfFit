# Add this new method to the UserService class

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