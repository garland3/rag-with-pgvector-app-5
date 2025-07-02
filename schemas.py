from pydantic import BaseModel
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: str | None = None
    picture: str | None = None

class UserCreate(UserBase):
    auth0_id: str

class UserUpdate(UserBase):
    pass


class User(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: str | None = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    name: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SearchQuery(BaseModel):
    text: str

class SearchResult(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    content: str

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str
