from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from config import settings
from typing import List, Tuple
import json


def llm_rerank_chunks(query: str, chunks: List, top_k: int = 10) -> List:
    """
    Rerank chunks using LLM-based relevance scoring.
    """
    if not chunks:
        return []
    
    # If we have fewer chunks than top_k, return all
    if len(chunks) <= top_k:
        return chunks
    
    chat = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.gemini_api_key)
    
    # Prepare chunks for evaluation
    chunk_texts = []
    for i, chunk in enumerate(chunks):
        chunk_texts.append(f"Chunk {i}: {chunk.content[:500]}")  # Limit chunk size for context
    
    # Create the reranking prompt
    system_prompt = """You are an expert at evaluating the relevance of text passages to search queries.
Your task is to score each chunk based on how relevant it is to the given query.

Rate each chunk on a scale of 0-10 where:
- 10: Highly relevant, directly answers the query
- 7-9: Very relevant, contains important information 
- 4-6: Somewhat relevant, contains related information
- 1-3: Slightly relevant, tangentially related
- 0: Not relevant at all

Return your response as a JSON array of scores in the same order as the chunks.
Example: [8, 3, 9, 1, 6]
"""
    
    human_prompt = f"""Query: {query}

Chunks to evaluate:
{chr(10).join(chunk_texts)}

Please score each chunk's relevance to the query and return only the JSON array of scores."""
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = chat(messages)
        
        # Parse the response to get scores
        scores = json.loads(response.content.strip())
        
        # Ensure we have the right number of scores
        if len(scores) != len(chunks):
            # Fallback: return original order if parsing fails
            return chunks[:top_k]
        
        # Create chunk-score pairs and sort by score
        chunk_score_pairs = list(zip(chunks, scores))
        chunk_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k chunks
        reranked_chunks = [chunk for chunk, score in chunk_score_pairs[:top_k]]
        
        # Add the reranking score to chunks for reference
        for i, (chunk, score) in enumerate(chunk_score_pairs[:top_k]):
            reranked_chunks[i].rerank_score = score
        
        return reranked_chunks
        
    except Exception as e:
        print(f"Error in LLM reranking: {e}")
        # Fallback to original order
        return chunks[:top_k]


def hybrid_search_and_rerank(db_session, project_id: str, query: str, 
                           initial_k: int = 50, final_k: int = 10) -> List:
    """
    Perform hybrid search: vector similarity + LLM reranking.
    
    1. Retrieve initial_k chunks using vector similarity
    2. Rerank using LLM to select final_k chunks
    """
    from crud.search_manager import search_chunks
    
    # Step 1: Get more chunks than we need using vector similarity
    initial_chunks = search_chunks(db_session, project_id, query, top_k=initial_k)
    
    if not initial_chunks:
        return []
    
    # Step 2: Rerank using LLM
    reranked_chunks = llm_rerank_chunks(query, initial_chunks, top_k=final_k)
    
    return reranked_chunks