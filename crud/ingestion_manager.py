from sqlalchemy.orm import Session
from models.ingestion_job import IngestionJob
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime


def create_ingestion_job(
    db: Session,
    project_id: str,
    user_id: str,
    total_files: int,
    file_metadata: List[Dict[str, Any]] = None
) -> IngestionJob:
    """
    Create a new ingestion job.
    """
    job_metadata = {
        "files": file_metadata or [],
        "started_at": datetime.utcnow().isoformat()
    }
    
    job = IngestionJob(
        project_id=project_id,
        user_id=user_id,
        total_files=total_files,
        job_metadata=job_metadata
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_ingestion_job(db: Session, job_id: str) -> Optional[IngestionJob]:
    """
    Get an ingestion job by ID.
    """
    return db.query(IngestionJob).filter(IngestionJob.id == job_id).first()


def get_jobs_by_user(db: Session, user_id: str, limit: int = 10) -> List[IngestionJob]:
    """
    Get recent ingestion jobs for a user.
    """
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.user_id == user_id)
        .order_by(IngestionJob.created_at.desc())
        .limit(limit)
        .all()
    )


def get_jobs_by_project(db: Session, project_id: str, limit: int = 10) -> List[IngestionJob]:
    """
    Get recent ingestion jobs for a project.
    """
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.project_id == project_id)
        .order_by(IngestionJob.created_at.desc())
        .limit(limit)
        .all()
    )


def update_job_status(
    db: Session, 
    job_id: str, 
    status: str, 
    error_message: str = None
) -> bool:
    """
    Update job status.
    """
    job = get_ingestion_job(db, job_id)
    if not job:
        return False
    
    job.status = status
    if error_message:
        job.error_message = error_message
    
    db.commit()
    return True


def update_job_progress(
    db: Session,
    job_id: str,
    processed_files: int,
    failed_files: int = None
) -> bool:
    """
    Update job progress.
    """
    job = get_ingestion_job(db, job_id)
    if not job:
        return False
    
    job.processed_files = processed_files
    if failed_files is not None:
        job.failed_files = failed_files
    
    db.commit()
    return True


def increment_job_progress(
    db: Session,
    job_id: str,
    success: bool = True
) -> bool:
    """
    Increment job progress by one file.
    """
    job = get_ingestion_job(db, job_id)
    if not job:
        return False
    
    job.processed_files += 1
    if not success:
        job.failed_files += 1
    
    # Auto-complete job if all files processed
    if job.processed_files >= job.total_files:
        job.status = "completed"
        if job.job_metadata:
            job.job_metadata["completed_at"] = datetime.utcnow().isoformat()
    
    db.commit()
    return True


def add_file_error(
    db: Session,
    job_id: str,
    filename: str,
    error_message: str
) -> bool:
    """
    Add error information for a specific file.
    """
    job = get_ingestion_job(db, job_id)
    if not job:
        return False
    
    if not job.job_metadata:
        job.job_metadata = {}
    
    if "file_errors" not in job.job_metadata:
        job.job_metadata["file_errors"] = []
    
    job.job_metadata["file_errors"].append({
        "filename": filename,
        "error": error_message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    db.commit()
    return True


def delete_old_jobs(db: Session, days_old: int = 30) -> int:
    """
    Delete ingestion jobs older than specified days.
    Returns count of deleted jobs.
    """
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    deleted_count = (
        db.query(IngestionJob)
        .filter(IngestionJob.created_at < cutoff_date)
        .delete()
    )
    
    db.commit()
    return deleted_count