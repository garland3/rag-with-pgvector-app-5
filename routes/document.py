from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from models.document import Document as DocumentModel
from models.project import Project as ProjectModel
from models.chunk import Chunk as ChunkModel
from schemas import Document
from database import SessionLocal
from rag.processing import get_text_chunks, get_embeddings
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/documents", response_model=Document)
async def upload_document(project_id: uuid.UUID, file: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    
    db_document = DocumentModel(name=file.filename, content=content, project_id=project_id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # For now, only handle text files
    if file.filename.endswith(".txt"):
        text = content.decode("utf-8")
        chunks = get_text_chunks(text)
        embeddings = get_embeddings(chunks)

        for i, chunk_content in enumerate(chunks):
            chunk = ChunkModel(
                document_id=db_document.id,
                content=chunk_content,
                embedding=embeddings[i]
            )
            db.add(chunk)
        db.commit()

    return db_document
