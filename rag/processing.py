from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
from config import settings
from typing import List


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using OpenAI-compatible API via requests.
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.embedding_model,
        "input": texts
    }
    
    response = requests.post(
        f"{settings.openai_base_url}/embeddings",
        headers=headers,
        json=data,
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"Embedding API error: {response.status_code} - {response.text}")
    
    result = response.json()
    return [item["embedding"] for item in result["data"]]


def get_completion(query: str, context: str) -> str:
    """
    Generate completion using OpenAI-compatible chat API via requests.
    """
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that answers questions based on the provided context."
        },
        {
            "role": "user", 
            "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        }
    ]
    
    data = {
        "model": settings.chat_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    response = requests.post(
        f"{settings.openai_base_url}/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"Chat API error: {response.status_code} - {response.text}")
    
    result = response.json()
    return result["choices"][0]["message"]["content"]
