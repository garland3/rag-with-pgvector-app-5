from sqlalchemy.orm import Session
from crud.search_manager import search_chunks
from rag.processing import get_completion
from rag.reranking import hybrid_search_and_rerank
from typing import Dict, List
import uuid


def get_chat_response(db: Session, project_id: uuid.UUID, query: str, use_reranking: bool = True) -> Dict:
    """
    Get chat response with source attribution.
    Returns a dictionary with response and sources.
    """
    # Choose search strategy based on reranking preference
    if use_reranking:
        chunks = hybrid_search_and_rerank(db, project_id, query, initial_k=50, final_k=10)
    else:
        chunks = search_chunks(db, project_id, query, top_k=10)
    
    if not chunks:
        return {
            "response": "I couldn't find any relevant information to answer your question.",
            "sources": []
        }
    
    # Prepare context with chunk references
    context_parts = []
    sources = []
    
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[Source {i+1}]: {chunk.content}")
        
        # Get document name for source attribution
        document = db.query(chunk.document).first() if hasattr(chunk, 'document') else None
        document_name = document.name if document else f"Document {chunk.document_id}"
        
        # Determine relevance score based on available information
        if hasattr(chunk, 'rerank_score'):
            relevance_score = chunk.rerank_score / 10.0  # Normalize to 0-1
        elif hasattr(chunk, 'distance'):
            relevance_score = 1.0 - chunk.distance  # Distance-based score
        else:
            relevance_score = 1.0 - (i * 0.1)  # Position-based fallback
        
        sources.append({
            "id": i + 1,
            "document_name": document_name,
            "document_id": str(chunk.document_id),
            "chunk_content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
            "relevance_score": max(0.0, min(1.0, relevance_score))  # Clamp to 0-1
        })
    
    context = "\n\n".join(context_parts)
    
    # Enhanced prompt with source instruction
    enhanced_query = f"""
Based on the provided sources, answer the following question. Please reference the sources in your answer using [Source X] notation.

Question: {query}

Context:
{context}

Please provide a comprehensive answer and indicate which sources support your response.
"""
    
    response = get_completion(enhanced_query, "")
    
    return {
        "response": response,
        "sources": sources
    }

