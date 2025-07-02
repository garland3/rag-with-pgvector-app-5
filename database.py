from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from .database_base import Base

# Import all models here to ensure they are registered with Base
from models.user import User
from models.project import Project
from models.document import Document
from models.chunk import Chunk

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
