from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.project_manager import get_project
from database import get_db
from models.user import User
from routes.document import process_documents_pipeline
from crud.ingestion_manager import create_ingestion_job
from utils.logging import get_logger, log_error
import tempfile
import os
from typing import List

router = APIRouter(prefix="/documents", tags=["document-upload"])
logger = get_logger(__name__)


@router.post("/upload/{project_id}", status_code=202)
async def upload_documents_to_project(
    project_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload multiple documents to a project (alternative endpoint for frontend).
    This endpoint matches the frontend call pattern: /documents/upload/{project_id}
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
            "total_size": total_size,
            "message": "Upload started successfully"
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