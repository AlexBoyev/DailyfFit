class User:
    def __init__(self, id, name, email, password, role):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role

class TrainingPlan:
    def __init__(self, id, goal, description, medical_clearance_required):
        self.id = id
        self.goal = goal
        self.description = description
        self.medical_clearance_required = medical_clearance_required

class NutritionMenu:
    def __init__(self, id, calories, type, description):
        self.id = id
        self.calories = calories
        self.type = type
        self.description = description

class Registration:
    def __init__(self, user_id, class_id, date):
        self.user_id = user_id
        self.class_id = class_id
        self.date = date
