# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Run the complete environment setup (includes PostgreSQL setup)
./setup.sh

# Manual installation of dependencies
pip install -r requirements.txt
pip install pgvector langchain langchain-openai
```

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Custom port and host
./run.sh --port 3000 --host 0.0.0.0

# Setup only (useful for CI/CD)
./run.sh --setup-only

# Skip setup and start server directly
./run.sh --skip-setup

# Manual start
python main.py

# Alternative using uvicorn directly
uvicorn main:app --reload --host localhost --port 8000
```

### Database Operations
```bash
# Run database migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Check database connection
python check_db.py
```

### PostgreSQL Database
- Database URL: `postgresql://postgres:password@localhost:5432/your_app_db`
- The setup script automatically enables the pgvector extension
- Use Docker Compose to start PostgreSQL: `docker-compose up -d`

## Architecture Overview

This is a multi-tenant RAG (Retrieval-Augmented Generation) application built with FastAPI that supports project-based knowledge bases with intelligent document retrieval.

### Current Implementation
- **Authentication**: OAuth 2.0 with JWT tokens (Auth0, Google, GitHub support)
- **Multi-tenancy**: Project-based access control with user ownership
- **Document Processing**: Upload, chunking, and vector embedding storage
- **RAG Pipeline**: Semantic search with Google Gemini for completions
- **Vector Storage**: PostgreSQL with pgvector extension

### Planned Architecture (see plan.md)
The application is designed to evolve into a more sophisticated system with:
- **Advanced Access Control**: Role-based permissions (owner, editor, viewer) and user groups
- **Enhanced RAG Pipeline**: Vector retrieval (K=150) → Reranking → Context selection (M=10)
- **Reranking System**: LLM-based relevance scoring or cross-encoder models
- **Rich UI**: React/Vue.js SPA with real-time chat and document management dashboard
- **Performance Features**: Background processing queues, analytics, and configurable parameters

### Current Data Flow
1. **Document Upload** → Text extraction → Chunking (1000 chars, 200 overlap)
2. **Embedding Generation** → Google Gemini embedding-001 model (768 dimensions)
3. **Vector Storage** → PostgreSQL with pgvector for similarity search
4. **Query Processing** → Semantic search → Context retrieval → Gemini completion

### Database Schema
- **Users**: OAuth identity management
- **Projects**: Multi-tenant containers with owner-based access
- **Documents**: File metadata within projects
- **Chunks**: Text segments with 768-dimensional embeddings

### Key Modules
- `auth/`: OAuth client, JWT management, authentication dependencies
- `models/`: SQLAlchemy models with UUID primary keys and pgvector integration
- `crud/`: Business logic managers for each entity type
- `routes/`: FastAPI routers organized by functionality
- `rag/processing.py`: Core RAG pipeline with LangChain integration

## Configuration

### Required Environment Variables
```bash
# OAuth (supports Auth0, Google, GitHub)
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
OAUTH_DOMAIN=your_oauth_domain

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# JWT
JWT_SECRET_KEY=your_jwt_secret_key

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_app_db
```

### OAuth Provider Configuration
The application uses a generic OAuth implementation that works with:
- **Auth0**: Auto-generates URLs from domain
- **Google**: Requires explicit OAuth URLs in environment
- **GitHub**: Requires explicit OAuth URLs in environment

See `docs/auth0-setup.md` for Auth0-specific configuration details.

## Development Patterns

### Model Relationships
- All models use UUID primary keys with `uuid.uuid4()` defaults
- Foreign key relationships use `UUID(as_uuid=True)`
- Use SQLAlchemy relationship declarations for ORM navigation

### Authentication Flow
- Routes can use `get_current_user` (required) or `get_current_user_optional`
- JWT tokens contain user_id (OAuth sub claim) for database lookups
- User records link OAuth identity to internal user management

### Vector Operations
- Embeddings are 768-dimensional vectors stored in pgvector
- Use raw SQL for similarity search with distance operators
- Chunk content is stored alongside embeddings for retrieval

### Error Handling
- The application has basic error handling but may need enhancement
- Database sessions are managed through FastAPI dependencies
- OAuth errors are handled in the auth flow with redirects

## Testing

No specific test framework is configured. Check if tests exist before assuming testing approach.