from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    total_files = Column(Integer, default=0, nullable=False)
    processed_files = Column(Integer, default=0, nullable=False)
    failed_files = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    error_message = Column(Text)
    job_metadata = Column(JSONB)  # Store file names, sizes, processing details
    
    # Relationships
    project = relationship("Project")
    user = relationship("User")
    
    def __repr__(self):
        return f"<IngestionJob {self.id} - {self.status}>"
    
    @property
    def progress_percentage(self):
        if self.total_files == 0:
            return 0
        return round((self.processed_files / self.total_files) * 100, 1)
    
    @property
    def success_rate(self):
        if self.processed_files == 0:
            return 0
        successful_files = self.processed_files - self.failed_files
        return round((successful_files / self.processed_files) * 100, 1)