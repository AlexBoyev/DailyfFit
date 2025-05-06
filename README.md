# DailyFit - Your Personal Training & Nutrition Solution

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🏋️ Project Overview

DailyFit is a comprehensive fitness application designed to help users create personalized training plans and nutrition menus based on their specific requirements and goals. Whether you're looking to lose weight, get fit, or gain muscle mass, DailyFit provides tailored solutions for your fitness journey.


## ✨ Key Features

- **Personalized Training Plans**: Create customized workout routines based on your fitness goals
- **Tailored Nutrition Menus**: Get diet recommendations matching your health requirements
- **Goal-based Programs**: Choose from specialized programs for weight loss, fitness, or muscle gain
- **Medical Considerations**: Accommodate specific medical conditions in your fitness journey
- **Class Registration**: Sign up for fitness classes directly through the platform
- **Communication Tools**: Contact gym staff through integrated messaging
- **Progress Tracking**: Monitor your fitness journey with comprehensive statistics

## 🔧 Technology Stack

- **Backend**: Python with FastAPI
- **Database**: MySQL
- **Containerization**: Docker & Docker Compose
- **Frontend**: React.js with Tailwind CSS
- **Authentication**: JWT-based secure login system
- **API**: RESTful architecture for frontend-backend communication

## 🏗️ Architecture

DailyFit follows a modern three-tier architecture:

1. **Frontend Layer**: React-based responsive UI
2. **API Layer**: FastAPI-powered backend services
3. **Data Layer**: MySQL database with optimized schema design

![Architecture Diagram](https://via.placeholder.com/800x400)

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AlexBoyev/dailyfit.git
   cd dailyfit
   ```

2. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   ```
   Frontend: http://localhost:3001
   API Documentation: http://localhost:8001/docs
   ```

## 📊 Database Schema

The MySQL database is structured with the following key tables:

- **Users**: User accounts and authentication details
- **UserProfiles**: Medical information and fitness preferences
- **TrainingPlans**: Workout routines categorized by goals
- **NutritionMenus**: Meal plans tailored to different requirements
- **Classes**: Available fitness classes with schedules
- **Registrations**: User registrations for classes
- **Messages**: Communication between users and staff

## 🔒 Security Features

DailyFit implements multiple layers of security:

- **User Authentication**: JWT-based secure login system
- **Role-based Access Control**: Different permissions for users, trainers, and administrators
- **Data Encryption**: Sensitive user data is encrypted
- **Input Validation**: All user inputs are validated to prevent injections
- **Docker Isolation**: Containerized components for enhanced security
- **Database Security**: Restricted access and parameterized queries

## 📁 Project Structure

< >

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

Project Link: [https://github.com/AlexBoyev/dailyfit](https://github.com/AlexBoyev/dailyfit)
