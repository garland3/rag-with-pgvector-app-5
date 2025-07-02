from sqlalchemy.orm import Session
from models.user import User
from schemas import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_auth0_id(db: Session, auth0_id: str):
    return db.query(User).filter(User.auth0_id == auth0_id).first()


def create_user(db: Session, user: UserCreate):
    db_user = User(
        auth0_id=user.auth0_id,
        email=user.email,
        name=user.name,
        picture=user.picture
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: User, updates: UserUpdate):
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
