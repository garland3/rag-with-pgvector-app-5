
import sqlalchemy
from sqlalchemy.exc import OperationalError

DATABASE_URL = "postgresql://postgres:password@localhost:5432/your_app_db"

def check_db_connection():
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("Database connection successful!")
            return True
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    check_db_connection()
