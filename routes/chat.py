from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.chat_manager import get_chat_response
from crud.project_manager import get_project
from database import get_db
from models.user import User
from schemas import ChatMessage, ChatResponse
import uuid

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    project_id: uuid.UUID,
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat with a project.
    """
    project = get_project(db, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    response_data = get_chat_response(db=db, project_id=project_id, query=message.text)
    return response_data
