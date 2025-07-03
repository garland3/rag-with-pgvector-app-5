from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from crud.ingestion_manager import get_ingestion_job, get_jobs_by_user
from database import get_db
from models.user import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the status of an ingestion job.
    """
    job = get_ingestion_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify user has access to this job
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": str(job.id),
        "status": job.status,
        "progress": {
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "failed_files": job.failed_files,
            "percentage": job.progress_percentage,
            "success_rate": job.success_rate
        },
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error_message": job.error_message,
        "metadata": job.job_metadata
    }


@router.get("/")
async def get_user_jobs(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent ingestion jobs for the current user.
    """
    jobs = get_jobs_by_user(db, str(current_user.id), limit)
    
    return [
        {
            "job_id": str(job.id),
            "project_id": str(job.project_id),
            "status": job.status,
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "failed_files": job.failed_files,
            "progress_percentage": job.progress_percentage,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
        for job in jobs
    ]