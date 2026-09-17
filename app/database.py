import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "meetplan"),
        user=os.getenv("DB_USER", "meetplan_user"),
        password=os.getenv("DB_PASSWORD", "meetplan_pass")
    )
    return conn