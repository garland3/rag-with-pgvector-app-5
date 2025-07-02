from sqlalchemy.orm import Session
from models.project import Project
from schemas import ProjectCreate
import uuid


def create_project(db: Session, project: ProjectCreate, owner_id: str):
    db_project = Project(**project.dict(), owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects_by_owner(db: Session, owner_id: str):
    return db.query(Project).filter(Project.owner_id == owner_id).all()


def get_project(db: Session, project_id: uuid.UUID):
    return db.query(Project).filter(Project.id == project_id).first()
