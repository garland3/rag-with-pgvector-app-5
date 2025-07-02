from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.search_manager import search_chunks
from crud.project_manager import get_project
from database import get_db
from models.user import User
from schemas import SearchQuery, SearchResult
import uuid
from typing import List

router = APIRouter(prefix="/projects/{project_id}/search", tags=["search"])


@router.post("/", response_model=List[SearchResult])
async def search(
    project_id: uuid.UUID,
    query: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for chunks in a project.
    """
    project = get_project(db, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    return search_chunks(db=db, project_id=project_id, query=query.text)
