# FastAPI OAuth Application

A simple, generic FastAPI application with OAuth 2.0 authentication that can work with any OAuth provider (Auth0, Google, GitHub, etc.).

## Features

- 🔐 Generic OAuth 2.0 implementation
- 🎯 Works with any OAuth provider (Auth0, Google, GitHub, etc.)
- 🔑 JWT token management
- 🛡️ Protected routes with authentication
- 📝 Simple HTML interface
- 🚀 FastAPI with automatic API documentation
- 🐳 Docker support included

## Project Structure

```
├── auth/                   # Authentication module
│   ├── __init__.py
│   ├── dependencies.py     # FastAPI dependencies for auth
│   ├── oauth_client.py     # Generic OAuth client
│   └── token_manager.py    # JWT token handling
├── routes/                 # API routes
│   ├── __init__.py
│   ├── api.py             # General API routes
│   └── auth.py            # Authentication routes
├── config.py              # Application configuration
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
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

Edit `.env` with your OAuth provider settings:

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
```

### 3. Provider-Specific Configuration

#### For Auth0:
```env
OAUTH_DOMAIN=your-tenant.auth0.com
OAUTH_CLIENT_ID=your_auth0_client_id
OAUTH_CLIENT_SECRET=your_auth0_client_secret
```

#### For Google:
```env
OAUTH_DOMAIN=accounts.google.com
OAUTH_AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token
OAUTH_USERINFO_URL=https://www.googleapis.com/oauth2/v2/userinfo
```

#### For GitHub:
```env
OAUTH_DOMAIN=github.com
OAUTH_AUTHORIZE_URL=https://github.com/login/oauth/authorize
OAUTH_TOKEN_URL=https://github.com/login/oauth/access_token
OAUTH_USERINFO_URL=https://api.github.com/user
```

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host localhost --port 8000
```

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

### 2. API Endpoints

- `GET /` - Home page with HTML interface
- `GET /auth/login` - Get OAuth login URL
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/me` - Get current user info (protected)
- `GET /api/protected` - Example protected route
- `GET /api/profile` - User profile endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

### 3. Example Usage with curl

```bash
# 1. Get login URL
curl http://localhost:8000/auth/login

# 2. Visit the returned auth_url in browser to complete OAuth

# 3. Use the returned token for protected endpoints
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/api/protected
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

## Development

The application uses:
- **FastAPI**: Modern, fast web framework
- **python-jose**: JWT handling
- **httpx**: Async HTTP client for OAuth requests
- **pydantic-settings**: Configuration management

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