-- sql/schema.sql

CREATE TABLE IF NOT EXISTS Users (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100),
    email            VARCHAR(100) UNIQUE,
    password_hash    VARCHAR(255),
    role             ENUM('user','admin'),
    address          VARCHAR(255),
    phone            VARCHAR(50),
    plan             VARCHAR(50) DEFAULT 'Free plan'
);

CREATE TABLE IF NOT EXISTS TrainingPlans (
    id                             INT AUTO_INCREMENT PRIMARY KEY,
    goal                           VARCHAR(50),
    description                    TEXT,
    medical_clearance_required     BOOLEAN
);

CREATE TABLE IF NOT EXISTS NutritionMenus (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    calories    INT,
    type        ENUM('weight_loss','muscle_gain','fitness'),
    description TEXT
);

CREATE TABLE IF NOT EXISTS ClassRegistrations (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT,
    class_id  INT,
    date      DATE
);
