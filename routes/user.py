from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from models.user import User as UserModel
from schemas import User
from database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users/me", response_model=User)
def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.auth0_id == current_user["user_id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
