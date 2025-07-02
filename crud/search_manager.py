from sqlalchemy.orm import Session
from sqlalchemy import text
from models.chunk import Chunk
from rag.processing import get_embeddings
import uuid


def search_chunks(db: Session, project_id: uuid.UUID, query: str, top_k: int = 10):
    """
    Search for chunks using native pgvector similarity search.
    """
    query_embedding = get_embeddings([query])[0]
    
    # Use native pgvector similarity search with cosine distance
    sql_query = text("""
        SELECT c.id, c.document_id, c.content, c.embedding,
               c.embedding <=> :query_embedding AS distance
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.project_id = :project_id
        ORDER BY distance ASC
        LIMIT :top_k
    """)
    
    result = db.execute(sql_query, {
        'query_embedding': str(query_embedding),
        'project_id': str(project_id), 
        'top_k': top_k
    })
    
    chunks = []
    for row in result:
        chunk = Chunk(
            id=row.id,
            document_id=row.document_id,
            content=row.content,
            embedding=row.embedding
        )
        chunk.distance = row.distance
        chunks.append(chunk)
    
    return chunks
