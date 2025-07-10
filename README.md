# RAG Application with pgvector

A multi-tenant RAG (Retrieval-Augmented Generation) application built with FastAPI that allows users to create knowledge bases from their documents and chat with them using natural language queries. Features OAuth 2.0 authentication, vector embeddings with pgvector, and intelligent document retrieval.

## Features

- 🔐 OAuth 2.0 authentication (Auth0, Google, GitHub)
- 🏢 Multi-tenant project-based knowledge bases
- � Document processing (PDF, DOCX, TXT, MD)
- 🧠 Vector embeddings with Google Gemini
- 🔍 Semantic search with pgvector
- � Chat interface with RAG pipeline
- 🔄 LLM-based reranking for improved results
- �️ PostgreSQL with pgvector extension
- 🧪 Comprehensive test suite

## Project Structure

```
├── auth/                   # Authentication module
│   ├── dependencies.py     # FastAPI auth dependencies
│   ├── oauth_client.py     # Generic OAuth client
│   └── token_manager.py    # JWT token handling
├── models/                 # SQLAlchemy models
│   ├── user.py            # User model
│   ├── project.py         # Project model
│   ├── document.py        # Document model
│   ├── chunk.py           # Text chunk with embeddings
│   └── ingestion_job.py   # Background job tracking
├── crud/                  # Business logic managers
│   ├── user_manager.py    # User operations
│   ├── project_manager.py # Project operations
│   ├── document_manager.py # Document operations
│   ├── chat_manager.py    # Chat operations
│   ├── search_manager.py  # Search operations
│   └── ingestion_manager.py # Document ingestion
├── routes/                # API routes
│   ├── auth.py            # Authentication endpoints
│   ├── project.py         # Project management
│   ├── document.py        # Document upload/management
│   ├── documents_upload.py # Document upload endpoints
│   ├── chat.py            # RAG chat interface
│   ├── search.py          # Search endpoints
│   ├── jobs.py            # Background job tracking
│   └── user.py            # User management
├── rag/                   # RAG pipeline
│   ├── document_processors.py  # PDF, DOCX, TXT processing
│   ├── processing.py      # Text chunking and embeddings
│   └── reranking.py       # LLM-based result reranking
├── migrations/            # Alembic database migrations
├── tests/                 # Comprehensive test suite
│   ├── test_auth.py       # Authentication tests
│   ├── test_projects.py   # Project management tests
│   ├── test_complete_pipeline.py  # End-to-end tests
│   ├── test_document_management.py # Document tests
│   ├── test_chat.py       # Chat functionality tests
│   ├── test_ingestion_pipeline.py # Ingestion tests
│   ├── test_uploaded_docs.py      # Document processing tests
│   └── test_docs/         # Sample test documents
├── scripts/               # Utility scripts
│   ├── run-tests.sh       # Test runner script
│   ├── run.sh             # Application runner
│   └── setup.sh           # Setup script
├── docs/                  # Documentation
│   ├── planning/          # Architecture and planning docs
│   ├── ingestion-plan.md  # Document ingestion pipeline plan
│   └── CLAUDE.md          # Development guide
├── utils/                 # Utilities
│   └── logging.py         # Logging configuration
├── config.py              # Application configuration
├── main.py                # FastAPI application
├── database.py            # Database connection
├── schemas.py             # Pydantic schemas
├── requirements.txt       # Python dependencies
├── requirements-test.txt  # Test dependencies
├── alembic.ini            # Database migration config
├── .env.example          # Environment variables template
└── docker-compose.yml    # PostgreSQL database
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure your OAuth provider:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# OAuth Configuration
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
OAUTH_DOMAIN=your_oauth_domain
OAUTH_CALLBACK_URL=http://localhost:8000/auth/callback

# JWT Configuration  
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_app_db

# Google AI Configuration (for embeddings and chat)
GOOGLE_API_KEY=your_google_api_key

# OpenAI Configuration (for reranking - optional)
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. Database Setup

Start PostgreSQL with pgvector extension:

```bash
docker-compose up -d
```

Run database migrations:

```bash
alembic upgrade head
```

### 4. Run the Application

Using the provided script (recommended):

```bash
./scripts/run.sh
```

Or manually:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host localhost --port 8000
```

## Architecture Overview

### RAG Pipeline

1. **Document Upload** → Text extraction → Chunking (1000 chars, 200 overlap)
2. **Embedding Generation** → Google Gemini embedding-001 model (1536 dimensions)
3. **Vector Storage** → PostgreSQL with pgvector for similarity search
4. **Query Processing** → Semantic search → LLM reranking → Context retrieval → Response generation

### Key Components

- **Multi-tenancy**: Project-based isolation with owner access control
- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown files
- **Vector Search**: pgvector-powered semantic similarity search
- **Reranking**: LLM-based relevance scoring for improved results
- **Background Jobs**: Asynchronous document processing with progress tracking

## API Endpoints

### Authentication
- `GET /auth/login` - Get OAuth login URL
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/me` - Get current user info

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details
- `GET /projects/{id}/dashboard` - Project dashboard UI

### Documents
- `POST /documents/upload/{project_id}` - Upload documents
- `GET /documents/project/{project_id}` - List project documents
- `DELETE /documents/{document_id}` - Delete document

### Chat
- `POST /chat/{project_id}` - RAG chat with project knowledge base

### Jobs
- `GET /jobs` - List ingestion jobs
- `GET /jobs/{job_id}` - Get job status

### Search
- `POST /search/{project_id}` - Semantic search in project

## Usage

### 1. Authentication Flow

1. **Initiate Login**: `GET /auth/login`
   - Returns an authorization URL
   - Redirect user to this URL to begin OAuth flow

2. **OAuth Callback**: `GET /auth/callback`
   - Handles the OAuth callback automatically
   - Returns JWT access token and user info

3. **Access Protected Routes**: Include JWT token in Authorization header
   ```
   Authorization: Bearer <your_jwt_token>
   ```

### 2. Creating a Knowledge Base

```bash
# 1. Authenticate and get token
curl http://localhost:8000/auth/login

# 2. Create a project
curl -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Knowledge Base", "description": "AI Research Documents"}' \
     http://localhost:8000/projects

# 3. Upload documents
curl -H "Authorization: Bearer <token>" \
     -F "files=@document.pdf" \
     http://localhost:8000/documents/upload/{project_id}

# 4. Chat with your documents
curl -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"message": "What are the key findings about AI?"}' \
     http://localhost:8000/chat/{project_id}
```

## Configuration Options

The application can be configured through environment variables or by modifying `config.py`:

- **OAuth URLs**: Override default URL patterns for custom providers
- **JWT Settings**: Configure token expiration and signing algorithm
- **Application Settings**: Host, port, debug mode

## Security Considerations

- Change `JWT_SECRET_KEY` in production
- Configure CORS properly for your domain
- Use HTTPS in production
- Implement proper session management (replace in-memory state storage)
- Add rate limiting and input validation
- Store sensitive data securely (not in memory)

## Extending the Application

### Adding New OAuth Providers

1. Set the appropriate URLs in your `.env` file
2. Modify `oauth_client.py` if custom authentication logic is needed
3. Update user info extraction in `token_manager.py` if field names differ

### Adding Database Integration

1. Add database models for users
2. Modify authentication flow to store/retrieve user data
3. Update JWT payload to include additional user information

### Adding More Features

- User management endpoints
- Role-based access control
- Refresh token support
- Session management
- API rate limiting

## Docker Support

Start the PostgreSQL database:

```bash
docker-compose up -d
```

## Testing

The application includes a comprehensive test suite located in the `tests/` directory.

### Running Tests

#### Using the Test Script (Recommended)

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific test categories
./scripts/run-tests.sh unit        # Unit tests only
./scripts/run-tests.sh api         # API tests only  
./scripts/run-tests.sh auth        # Authentication tests only
./scripts/run-tests.sh coverage    # Tests with coverage report
./scripts/run-tests.sh ci          # CI-friendly test run
```

#### Using pytest directly

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test markers
pytest -m "unit"           # Unit tests
pytest -m "api"            # API tests
pytest -m "auth"           # Authentication tests
pytest -m "integration"    # Integration tests
```

### Test Structure

- `tests/test_auth.py` - Authentication tests
- `tests/test_chat.py` - Chat functionality tests
- `tests/test_document_management.py` - Document management tests
- `tests/test_ingestion_pipeline.py` - Document ingestion tests
- `tests/test_project_dashboard.py` - Dashboard tests
- `tests/test_projects.py` - Project management tests
- `tests/conftest.py` - Test configuration and fixtures
- `tests/test_docs/` - Sample documents for testing

### Test Categories

The test suite uses pytest markers to categorize tests:

- `unit` - Fast unit tests
- `integration` - Integration tests
- `api` - API endpoint tests
- `auth` - Authentication tests
- `slow` - Longer running tests

## Security Scanning

The project includes security scanning with Bandit to identify potential security issues.

### Running Security Scans

```bash
# Install bandit
pip install bandit

# Run security scan (uses .bandit configuration)
bandit -c .bandit -r .

# Generate JSON report
bandit -c .bandit -r . -f json -o bandit-report.json

# Scan specific directories
bandit -c .bandit -r ./routes ./crud ./rag
```

### Configuration

Security scanning is configured via `.bandit` file which:
- Skips B101 (assert_used) for test files where assertions are expected
- Skips B608 (hardcoded_sql_expressions) for HTML template generation false positives
- Uses `# nosec` comments for legitimate test credentials and exception handling

### CI/CD Integration

Security scanning runs automatically in the CI/CD pipeline as part of the `security` job alongside safety checks for dependency vulnerabilities.

## Development

### Key Technologies

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with PostgreSQL
- **pgvector**: Vector similarity search
- **Google Gemini**: Embeddings and chat completions
- **LangChain**: RAG pipeline components
- **Alembic**: Database migrations
- **pytest**: Testing framework

### Development Commands

```bash
# Run with auto-reload
./scripts/run.sh

# Create database migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Run security scan
bandit -c .bandit -r .
```

## Current Limitations & Roadmap

### ✅ Implemented
- Basic OAuth authentication with JWT
- Multi-tenant project management
- Document upload and processing (PDF, DOCX, TXT, MD)
- Vector embeddings with semantic search
- RAG chat interface with reranking
- Comprehensive test suite

### 🔄 In Progress
- Asynchronous document processing pipeline
- Enhanced progress tracking for uploads
- Improved error handling and recovery

### 📋 Planned
- Modern React/Vue.js frontend
- Advanced access control (roles, groups)
- Analytics dashboard
- Real-time chat with WebSockets
- Enhanced document management UI
- Background job queue system

See `docs/planning/plan.md` for detailed roadmap and `docs/ingestion-plan.md` for the document ingestion pipeline plan.

## Troubleshooting

1. **Import Errors**: Install dependencies with `pip install -r requirements.txt`
2. **OAuth Errors**: Check your provider configuration and callback URL
3. **Token Errors**: Verify JWT secret key and token format
4. **CORS Issues**: Configure CORS middleware for your frontend domain

## License

This project is open source and available under the MIT License.


# Claude code. 

```
npm install -g @anthropic-ai/claude-code

claude
```