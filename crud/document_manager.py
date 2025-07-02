from sqlalchemy.orm import Session
from models.document import Document
from schemas import DocumentCreate
import uuid


def create_document(db: Session, document: DocumentCreate, project_id: uuid.UUID, content: bytes):
    db_document = Document(**document.dict(), project_id=project_id, content=content)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_documents_by_project(db: Session, project_id: uuid.UUID):
    return db.query(Document).filter(Document.project_id == project_id).all()
