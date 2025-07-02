from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from models.chunk import Chunk as ChunkModel
from schemas import ChatMessage, ChatResponse
from database import SessionLocal
from rag.processing import get_embeddings
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    query_embedding = get_embeddings([message.text])[0]
    
    results = db.query(ChunkModel).order_by(ChunkModel.embedding.l2_distance(query_embedding)).limit(5).all()
    
    context = ""
    for result in results:
        context += result.content + "\n\n"
        
    chat = ChatOpenAI(openai_api_key=settings.gemini_api_key)
    
    messages = [
        SystemMessage(content="You are a helpful assistant that answers questions based on the provided context."),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {message.text}\n\nAnswer:")
    ]
    
    response = chat(messages)
    
    return {"response": response.content}
