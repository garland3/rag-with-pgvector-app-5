from sqlalchemy.orm import Session
from models.chunk import Chunk
from rag.processing import get_embeddings
import numpy as np


def search_chunks(db: Session, project_id: str, query: str, top_k: int = 10):
    query_embedding = get_embeddings([query])[0]
    
    # This is a placeholder for a more efficient search
    chunks = db.query(Chunk).join(Chunk.document).filter(Chunk.document.has(project_id=project_id)).all()
    
    if not chunks:
        return []
        
    embeddings = np.array([chunk.embedding for chunk in chunks])
    similarities = np.dot(embeddings, query_embedding)
    
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    
    return [chunks[i] for i in top_k_indices]
