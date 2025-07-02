from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.project_manager import create_project as create_project_crud, get_projects_by_owner
from database import get_db
from models.user import User
from schemas import Project, ProjectCreate
from typing import List

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project.
    """
    return create_project_crud(db=db, project=project, owner_id=current_user.id)


@router.get("/", response_model=List[Project])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all projects for the current user.
    """
    return get_projects_by_owner(db=db, owner_id=current_user.id)
