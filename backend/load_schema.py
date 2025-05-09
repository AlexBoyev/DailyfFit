# backend/load_schema.py
import mysql.connector, os
from dotenv import load_dotenv

load_dotenv()
SQL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql"))

def ensure_schema():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=5
    )
    cur = conn.cursor()

    # 1) Create tables if missing
    sql = open(SQL_PATH, "r", encoding="utf-8").read()
    for stmt in sql.strip().split(";"):
        if stmt.strip():
            cur.execute(stmt)

    # 2) Add columns if missing (no DROP)
    for col, typ in [("address","VARCHAR(255)"),("phone","VARCHAR(50)")]:
        try:
            cur.execute(f"ALTER TABLE Users ADD COLUMN {col} {typ};")
        except mysql.connector.Error as e:
            if e.errno != 1060:  # ignore 'column exists'
                raise

    conn.commit()
    cur.close()
    conn.close()
