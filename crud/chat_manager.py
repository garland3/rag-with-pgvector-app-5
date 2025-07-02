from sqlalchemy.orm import Session
from crud.search_manager import search_chunks
from rag.processing import get_completion


def get_chat_response(db: Session, project_id: str, query: str):
    chunks = search_chunks(db, project_id, query)
    
    if not chunks:
        return "I couldn't find any relevant information to answer your question."
        
    context = "\n".join([chunk.content for chunk in chunks])
    
    return get_completion(query, context)

