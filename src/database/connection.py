import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


if __name__ == "__main__":
    # Test the connection
    try:
        with get_connection() as conn:
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
