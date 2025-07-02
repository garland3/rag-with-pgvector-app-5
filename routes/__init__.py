from .auth import router as auth_router
from .api import router as api_router
from .user import router as user_router
from .project import router as project_router
from .document import router as document_router
from .search import router as search_router
from .chat import router as chat_router

__all__ = [
    "auth_router",
    "api_router", 
    "user_router",
    "project_router",
    "document_router",
    "search_router",
    "chat_router"
]