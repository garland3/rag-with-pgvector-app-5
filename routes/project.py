from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from models.project import Project as ProjectModel
from models.user import User as UserModel
from schemas import Project, ProjectCreate
from database import SessionLocal
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects", response_model=Project)
def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.auth0_id == current_user["user_id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_project = ProjectModel(**project.dict(), owner_id=user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/{project_id}", response_model=Project)
def read_project(project_id: uuid.UUID, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
