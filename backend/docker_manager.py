import subprocess
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def is_docker_running():
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_container_running():
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=dailyfit-mysql"],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

def initialize_docker():
    try:
        # Get the project root directory
        project_root = Path(__file__).resolve().parent.parent
        
        # Run docker-compose up
        subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=project_root,
            check=True
        )
        
        # Wait for MySQL to be ready
        print("Waiting for MySQL to be ready...")
        max_attempts = 30
        attempt = 0
        
        # Get MySQL credentials from environment
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "yourpassword")
        
        while attempt < max_attempts:
            try:
                subprocess.run(
                    ["docker", "exec", "dailyfit-mysql", "mysqladmin", "ping", 
                     "-h", "localhost", 
                     "-u", db_user, 
                     f"-p{db_password}"],
                    capture_output=True,
                    check=True
                )
                print("MySQL is ready!")
                return True
            except subprocess.CalledProcessError:
                attempt += 1
                time.sleep(1)
        
        print("Error: MySQL did not become ready in time")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error initializing Docker: {str(e)}")
        return False

def ensure_schema_loaded():
    try:
        from load_schema import ensure_schema
        ensure_schema()
        return True
    except Exception as e:
        print(f"Error loading schema: {str(e)}")
        return False