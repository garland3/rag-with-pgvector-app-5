from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.document_manager import (
    create_document as create_document_crud,
    get_documents_by_project,
)
from crud.project_manager import get_project
from database import get_db
from models.user import User
from models.chunk import Chunk as ChunkModel
from schemas import Document, DocumentCreate
from rag.processing import get_text_chunks, get_embeddings
import uuid
from typing import List

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


@router.post("/", response_model=Document)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document to a project.
    """
    project = get_project(db, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    document_create = DocumentCreate(name=file.filename)
    db_document = create_document_crud(
        db=db, document=document_create, project_id=project_id, content=content
    )

    # For now, only handle text files
    if file.filename.endswith(".txt"):
        text = content.decode("utf-8")
        chunks = get_text_chunks(text)
        embeddings = get_embeddings(chunks)

        for i, chunk_content in enumerate(chunks):
            chunk = ChunkModel(
                document_id=db_document.id,
                content=chunk_content,
                embedding=embeddings[i],
            )
            db.add(chunk)
        db.commit()

    return db_document


@router.get("/", response_model=List[Document])
def get_documents(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all documents for a project.
    """
    project = get_project(db, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return get_documents_by_project(db=db, project_id=project_id)
