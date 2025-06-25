import os
import random
import json
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv
from database import get_connection

load_dotenv()
fake = Faker()

TRAINERS = ["Jordan", "Ava", "Liam", "Mia", "Noah"]
MEMBERSHIP_PLANS = ['bronze', 'silver', 'gold', 'platinum']
MEAL_TYPES = ['breakfast', 'lunch', 'dinner']
FOOD_ITEMS = {
    'breakfast': ['Oatmeal', 'Greek Yogurt', 'Eggs', 'Smoothie', 'Avocado Toast'],
    'lunch': ['Grilled Chicken', 'Salmon Bowl', 'Quinoa Salad', 'Turkey Wrap', 'Veggie Stir-Fry'],
    'dinner': ['Steak', 'Pasta', 'Grilled Fish', 'Stuffed Peppers', 'Burger']
}
PLAN_TYPES = ['weight_loss', 'muscle_gain', 'fitness']
DIET_TYPES = ['vegan', 'vegetarian', 'keto', 'paleo', 'none']
CLASS_STATUSES = ['registered', 'attended', 'missed']

def get_class_details(cur):
    cur.execute("""
        SELECT id, schedule_day, schedule_time, capacity 
        FROM Classes 
        WHERE is_active=1
    """)
    return cur.fetchall()

def create_user(cur):
    name = fake.name()
    email = fake.unique.email()
    password_hash = fake.sha256()
    role = 'user'
    address = fake.address().replace('\n', ', ')
    phone = fake.phone_number()
    profile_picture = fake.image_url(width=200, height=200)
    height_cm = random.randint(150, 200)
    weight_kg = random.randint(50, 120)
    age = random.randint(18, 65)
    gender = random.choice(['male', 'female', 'other'])
    membership_plan = random.choice(MEMBERSHIP_PLANS)
    signup_date = fake.date_time_between(start_date='-30d', end_date='-14d')
    last_login = fake.date_time_between(start_date=signup_date, end_date='now')
    is_active = True
    fitness_level = random.choice(['beginner', 'intermediate', 'advanced'])
    medical_conditions = fake.text(max_nb_chars=100)
    preferred_training_time = random.choice(['morning', 'afternoon', 'evening'])
    trainer_name = random.choice(TRAINERS + [None]*2)  # ~33% chance of no trainer

    cur.execute("""
        INSERT INTO Users
        (name, email, password_hash, role, address, phone, profile_picture,
         height_cm, weight_kg, age, gender, membership_plan, signup_date,
         last_login, is_active, fitness_level, medical_conditions,
         preferred_training_time, trainer_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, email, password_hash, role, address, phone, profile_picture,
          height_cm, weight_kg, age, gender, membership_plan, signup_date,
          last_login, is_active, fitness_level, medical_conditions,
          preferred_training_time, trainer_name))
    return cur.lastrowid

def create_nutrition_menu(cur, user_id):
    plan_type = random.choice(PLAN_TYPES)
    title = f"{plan_type.replace('_', ' ').title()} Plan"
    calories = random.randint(1600, 3000)
    description = fake.sentence(nb_words=12)
    meal_plan = json.dumps({
        "meals": [
            random.choice(FOOD_ITEMS['breakfast']),
            random.choice(FOOD_ITEMS['lunch']),
            random.choice(FOOD_ITEMS['dinner'])
        ]
    })
    diet_type = random.choice(DIET_TYPES)
    protein_grams = random.randint(80, 180)
    carbs_grams = random.randint(100, 350)
    fat_grams = random.randint(40, 100)
    cur.execute("""
        INSERT INTO NutritionMenus
        (user_id, title, calories, type, description, meal_plan, diet_type,
         protein_grams, carbs_grams, fat_grams)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, title, calories, plan_type, description, meal_plan, diet_type,
          protein_grams, carbs_grams, fat_grams))

def create_nutrition_logs(cur, user_id):
    today = datetime.now().date()
    for days_ago in range(14, 0, -1):
        log_date = today - timedelta(days=days_ago)
        for meal_type in MEAL_TYPES:
            calories = random.randint(300, 800)
            protein = random.randint(15, 50)
            carbs = random.randint(20, 100)
            fat = random.randint(10, 40)
            notes = f"Ate {random.choice(FOOD_ITEMS[meal_type])} for {meal_type}"
            cur.execute("""
                INSERT INTO NutritionLogs
                (user_id, date, meal_type, calories, protein_grams, carbs_grams, fat_grams, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, log_date, meal_type, calories, protein, carbs, fat, notes))


def create_class_registration(cur, user_id, class_details):
    """
    Improved registration logic that tries multiple classes and dates
    """
    import random
    from datetime import datetime, timedelta

    if not class_details or random.random() < 0.05:  # 5% skip chance
        return

    today = datetime.now().date()
    registered_count = 0
    max_registrations = random.randint(1, 3)  # Each user can register for 1-3 classes

    # Shuffle classes for fair distribution
    available_classes = list(class_details)
    random.shuffle(available_classes)

    for class_id, schedule_day, schedule_time, capacity in available_classes:
        if registered_count >= max_registrations:
            break

        # Find all valid dates in the last 14 days for this class
        valid_dates = []
        for days_ago in range(14):
            check_date = today - timedelta(days=days_ago)
            if check_date.strftime('%A').lower() == schedule_day.lower():
                valid_dates.append(check_date)

        # Try each valid date for this class
        for reg_date in valid_dates:
            # Check if user already registered for this class on this date
            cur.execute("""
                SELECT 1 FROM ClassRegistrations 
                WHERE user_id = %s AND class_id = %s AND date = %s
            """, (user_id, class_id, reg_date))

            if cur.fetchone():
                continue  # Already registered

            # Check capacity for this class/date
            cur.execute("""
                SELECT COUNT(*) FROM ClassRegistrations
                WHERE class_id = %s AND date = %s
            """, (class_id, reg_date))

            current_registrations = cur.fetchone()[0]

            if current_registrations < capacity:
                # Register for this class
                status = random.choice(['registered', 'attended', 'missed'])
                notes = f"Registered for {schedule_day} class"

                try:
                    cur.execute("""
                        INSERT INTO ClassRegistrations
                        (user_id, class_id, date, status, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, class_id, reg_date, status, notes))

                    registered_count += 1
                    break  # Move to next class

                except Exception as e:
                    print(f"Registration failed for user {user_id}, class {class_id}: {e}")
                    continue

    if registered_count == 0:
        print(f"Warning: User {user_id} could not be registered for any classes")


def main():
    conn = get_connection()
    cur = conn.cursor()

    # Count existing users
    cur.execute("SELECT COUNT(*) FROM Users WHERE role='user'")
    user_count = cur.fetchone()[0]
    needed = 30 - user_count

    if needed <= 0:
        print("Database already has 30 or more users.")
        cur.close()
        conn.close()
        return

    print(f"Populating {needed} users...")
    class_details = get_class_details(cur)

    for i in range(needed):
        user_id = create_user(cur)
        create_nutrition_menu(cur, user_id)
        create_nutrition_logs(cur, user_id)
        create_class_registration(cur, user_id, class_details)

        if (i + 1) % 5 == 0:  # Progress indicator
            print(f"Created {i + 1}/{needed} users...")

        conn.commit()

    # Verify registrations
    cur.execute("""
        SELECT c.name, COUNT(cr.id) as registered, c.capacity
        FROM Classes c
        LEFT JOIN ClassRegistrations cr ON c.id = cr.class_id
        GROUP BY c.id
    """)

    print("\nClass registration summary:")
    for name, registered, capacity in cur.fetchall():
        print(f"  {name}: {registered}/{capacity}")

    cur.close()
    conn.close()
    print("Done. Database populated with demo users and data.")

if __name__ == "__main__":
    main()
