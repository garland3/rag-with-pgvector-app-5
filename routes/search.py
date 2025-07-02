from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import get_current_user
from models.chunk import Chunk as ChunkModel
from schemas import SearchQuery, SearchResult
from database import SessionLocal
from rag.processing import get_embeddings
import numpy as np

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/search", response_model=list[SearchResult])
async def search(query: SearchQuery, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    query_embedding = get_embeddings([query.text])[0]
    
    results = db.query(ChunkModel).order_by(ChunkModel.embedding.l2_distance(query_embedding)).limit(10).all()
    
    return results
