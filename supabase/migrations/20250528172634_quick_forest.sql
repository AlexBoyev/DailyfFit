-- sql/schema.sql

CREATE TABLE IF NOT EXISTS Users (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    name                  VARCHAR(100),
    email                 VARCHAR(100) UNIQUE,
    password_hash         VARCHAR(255),
    role                  ENUM('user','admin'),
    address               VARCHAR(255),
    phone                 VARCHAR(50),
    profile_picture       VARCHAR(255),
    height_cm             INT,
    weight_kg             INT,
    age                   INT,
    gender               ENUM('male', 'female', 'other'),
    membership_plan       VARCHAR(100) DEFAULT 'Free membership',
    signup_date          DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login           DATETIME,
    is_active            BOOLEAN DEFAULT TRUE,
    fitness_level        ENUM('beginner', 'intermediate', 'advanced'),
    medical_conditions   TEXT,
    preferred_training_time ENUM('morning', 'afternoon', 'evening'),
    trainer_name         VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS TrainingPlans (
    id                             INT AUTO_INCREMENT PRIMARY KEY,
    goal                           VARCHAR(50),
    description                    TEXT,
    medical_clearance_required     BOOLEAN,
    created_at                     DATETIME DEFAULT CURRENT_TIMESTAMP,
    difficulty_level               ENUM('beginner', 'intermediate', 'advanced'),
    duration_weeks                 INT,
    sessions_per_week             INT
);

CREATE TABLE IF NOT EXISTS NutritionMenus (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(100),
    calories        INT,
    type            ENUM('weight_loss','muscle_gain','fitness'),
    description     TEXT,
    meal_plan       JSON,
    diet_type       ENUM('vegan', 'vegetarian', 'keto', 'paleo', 'none'),
    protein_grams   INT,
    carbs_grams     INT,
    fat_grams       INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Classes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100),
    description     TEXT,
    instructor      VARCHAR(100),
    capacity        INT,
    duration_mins   INT,
    difficulty      ENUM('beginner', 'intermediate', 'advanced'),
    schedule_time   TIME,
    schedule_day    ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'),
    room_location   VARCHAR(50),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ClassRegistrations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    class_id        INT,
    date            DATE,
    status          ENUM('registered','cancelled','attended','missed'),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (class_id) REFERENCES Classes(id)
);

CREATE TABLE IF NOT EXISTS UserProgress (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    date            DATE,
    weight_kg       FLOAT,
    body_fat_pct    FLOAT,
    muscle_mass_kg  FLOAT,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS WorkoutLogs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    training_plan_id INT,
    date            DATE,
    duration_mins   INT,
    calories_burned INT,
    workout_type    VARCHAR(50),
    notes           TEXT,
    rating          INT CHECK (rating BETWEEN 1 AND 5),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (training_plan_id) REFERENCES TrainingPlans(id)
);

CREATE TABLE IF NOT EXISTS NutritionLogs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    date            DATE,
    meal_type       ENUM('breakfast', 'lunch', 'dinner', 'snack'),
    calories        INT,
    protein_grams   INT,
    carbs_grams     INT,
    fat_grams       INT,
    notes           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);