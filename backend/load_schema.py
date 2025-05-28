import mysql.connector
from mysql.connector import Error
import os
import time
from dotenv import load_dotenv

load_dotenv()
SQL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql"))

def ensure_schema():
    print("⏳ Attempting to connect to MySQL...")

    for attempt in range(10):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                connection_timeout=5
            )
            if conn.is_connected():
                print("✅ Connected to MySQL.")
                break
        except Error as e:
            print(f"⚠️  Attempt {attempt + 1} failed: {e}")
            time.sleep(3)
    else:
        print("❌ Could not connect to MySQL after 10 attempts. Exiting.")
        return

    try:
        cur = conn.cursor()
        print("📄 Loading schema...")
        sql = open(SQL_PATH, "r", encoding="utf-8").read()
        for stmt in sql.strip().split(";"):
            if stmt.strip():
                cur.execute(stmt)

        conn.commit()
        cur.close()
        print("✅ Schema loaded successfully.")
    except Error as e:
        print(f"❌ Error loading schema: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    ensure_schema()
