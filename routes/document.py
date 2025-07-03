from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.document_manager import (
    create_document as create_document_crud,
    get_documents_by_project,
)
from crud.project_manager import get_project
from crud.ingestion_manager import (
    create_ingestion_job,
    update_job_status,
    increment_job_progress,
    add_file_error
)
from database import get_db
from models.user import User
from models.document import Document
from models.chunk import Chunk as ChunkModel
from schemas import Document as DocumentSchema, DocumentCreate
from rag.processing import get_text_chunks, get_embeddings
from rag.document_processors import process_document
from utils.logging import get_logger, log_document_upload, log_error
import uuid
import time
import os
import tempfile
from typing import List

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])
logger = get_logger(__name__)


@router.post("/", response_model=DocumentSchema)
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


@router.get("/", response_model=List[DocumentSchema])
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


@router.delete("/{document_id}")
def delete_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and all its associated chunks.
    """
    try:
        # Verify project exists and user has access
        project = get_project(db, project_id)
        if not project or project.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get the document to verify it exists and belongs to the project
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.project_id == project_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete all chunks associated with this document
        chunks_deleted = db.query(ChunkModel).filter(
            ChunkModel.document_id == document_id
        ).delete()

        # Delete the document
        db.delete(document)
        db.commit()

        logger.info(f"Deleted document {document_id} and {chunks_deleted} chunks for project {project_id}")

        return {
            "message": "Document deleted successfully",
            "document_id": str(document_id),
            "chunks_deleted": chunks_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(logger, e, {
            "document_id": str(document_id),
            "project_id": str(project_id),
            "user_id": str(current_user.id)
        })
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.post("/upload", status_code=202)
async def upload_multiple_documents(
    project_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload multiple documents to a project (bulk upload with background processing).
    """
    try:
        # Verify project exists and user has access
        project = get_project(db, project_id)
        if not project or project.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Project not found")

        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Prepare file metadata for job tracking
        file_metadata = []
        total_size = 0
        
        for file in files:
            content = await file.read()
            file_size = len(content)
            total_size += file_size
            
            # Reset file pointer for later processing
            await file.seek(0)
            
            file_metadata.append({
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type
            })

        # Create ingestion job
        job = create_ingestion_job(
            db=db,
            project_id=str(project_id),
            user_id=str(current_user.id),
            total_files=len(files),
            file_metadata=file_metadata
        )

        # Create temporary directory for this job
        temp_dir = tempfile.mkdtemp(prefix=f"ingestion_{job.id}_")
        
        # Save files to temp directory
        file_paths = []
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_paths.append(file_path)

        # Queue background processing
        background_tasks.add_task(
            process_documents_pipeline,
            str(job.id),
            file_paths,
            str(project_id),
            str(current_user.id),
            temp_dir
        )

        logger.info(f"Started bulk upload job {job.id} for {len(files)} files")

        return {
            "job_id": str(job.id),
            "status": "queued",
            "total_files": len(files),
            "total_size": total_size
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(logger, e, {
            "project_id": str(project_id),
            "user_id": str(current_user.id),
            "file_count": len(files) if files else 0
        })
        raise HTTPException(status_code=500, detail="Failed to start upload processing")


async def process_documents_pipeline(
    job_id: str,
    file_paths: List[str],
    project_id: str,
    user_id: str,
    temp_dir: str
):
    """
    Background task to process multiple documents.
    """
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Update job status to processing
        update_job_status(db, job_id, "processing")
        logger.info(f"Started processing job {job_id} with {len(file_paths)} files")

        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                logger.info(f"Processing file {filename} for job {job_id}")
                
                # Process single document
                await process_single_document_async(
                    db, file_path, project_id, job_id
                )
                
                # Increment progress (success)
                increment_job_progress(db, job_id, success=True)
                logger.info(f"Successfully processed {filename} for job {job_id}")

            except Exception as e:
                filename = os.path.basename(file_path)
                error_msg = str(e)
                
                # Log file-specific error
                add_file_error(db, job_id, filename, error_msg)
                increment_job_progress(db, job_id, success=False)
                
                log_error(logger, e, {
                    "job_id": job_id,
                    "filename": filename,
                    "project_id": project_id
                })

        # Job completion is handled automatically in increment_job_progress
        logger.info(f"Completed processing job {job_id}")

    except Exception as e:
        # Mark entire job as failed
        update_job_status(db, job_id, "failed", str(e))
        log_error(logger, e, {
            "job_id": job_id,
            "project_id": project_id
        })
    finally:
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory for job {job_id}")
        except Exception as e:
            log_error(logger, e, {"job_id": job_id, "temp_dir": temp_dir})
        
        db.close()


async def process_single_document_async(
    db: Session,
    file_path: str,
    project_id: str,
    job_id: str
):
    """
    Process a single document file (async version of existing logic).
    """
    # Read file content
    with open(file_path, "rb") as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    file_size = len(content)
    
    start_time = time.time()
    
    # Process document to extract text
    text, success, file_type = process_document(content, filename)
    
    if not success:
        raise Exception(f"Failed to process file {filename}. Supported formats: PDF, DOCX, TXT, MD")
    
    if not text.strip():
        raise Exception(f"No text content found in {filename}")
    
    # Create document record
    document_create = DocumentCreate(name=filename)
    db_document = create_document_crud(
        db=db, document=document_create, project_id=project_id, content=content
    )

    # Process text into chunks and embeddings
    chunks = get_text_chunks(text)
    embeddings = get_embeddings(chunks)

    # Store chunks with metadata
    for i, chunk_content in enumerate(chunks):
        chunk = ChunkModel(
            document_id=db_document.id,
            content=chunk_content,
            embedding=embeddings[i],
        )
        db.add(chunk)
    
    db.commit()
    
    # Log successful processing
    processing_time = time.time() - start_time
    log_document_upload(
        logger,
        document_id=str(db_document.id),
        filename=filename,
        file_size=file_size,
        processing_time=processing_time,
        chunk_count=len(chunks),
        user_id=project_id  # Using project_id as we don't have user_id in this context
    )
