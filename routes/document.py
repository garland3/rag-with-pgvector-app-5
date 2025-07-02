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
from rag.document_processors import process_document
from utils.logging import get_logger, log_document_upload, log_error
import uuid
import time
from typing import List

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])
logger = get_logger(__name__)


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
    start_time = time.time()
    
    try:
        project = get_project(db, project_id)
        if not project or project.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Project not found")

        content = await file.read()
        file_size = len(content)
        
        # Process document to extract text
        text, success, file_type = process_document(content, file.filename)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Failed to process file. Supported formats: PDF, DOCX, TXT, MD"
            )
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text content found in the document"
            )
        
        document_create = DocumentCreate(name=file.filename)
        db_document = create_document_crud(
            db=db, document=document_create, project_id=project_id, content=content
        )

        # Process text into chunks and embeddings
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
        
        # Log successful upload
        processing_time = time.time() - start_time
        log_document_upload(
            logger,
            document_id=str(db_document.id),
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time,
            chunk_count=len(chunks),
            user_id=str(current_user.id)
        )

        return db_document
        
    except HTTPException:
        # Re-raise HTTP exceptions without logging as errors
        raise
    except Exception as e:
        # Log unexpected errors
        log_error(logger, e, {
            "filename": file.filename,
            "project_id": str(project_id),
            "user_id": str(current_user.id)
        })
        raise HTTPException(status_code=500, detail="Internal server error during document processing")


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
