# Auth0 Configuration Example

This file shows how to configure the application specifically for Auth0.

## Auth0 Setup

1. **Create an Auth0 Application**:
   - Go to [Auth0 Dashboard](https://manage.auth0.com/)
   - Create a new "Regular Web Application"
   - Note your Domain, Client ID, and Client Secret

2. **Configure Callback URLs**:
   - In your Auth0 application settings, add:
   - Allowed Callback URLs: `http://localhost:8000/auth/callback`
   - Allowed Logout URLs: `http://localhost:8000/`
   - Allowed Web Origins: `http://localhost:8000`

3. **Update your .env file**:

```env
# Auth0 Configuration
OAUTH_CLIENT_ID=your_auth0_client_id
OAUTH_CLIENT_SECRET=your_auth0_client_secret
OAUTH_DOMAIN=your-tenant.auth0.com
OAUTH_CALLBACK_URL=http://localhost:8000/auth/callback

# The application will automatically generate these URLs for Auth0:
# OAUTH_AUTHORIZE_URL=https://your-tenant.auth0.com/authorize
# OAUTH_TOKEN_URL=https://your-tenant.auth0.com/oauth/token
# OAUTH_USERINFO_URL=https://your-tenant.auth0.com/userinfo

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
APP_HOST=localhost
APP_PORT=8000
APP_DEBUG=True
```

## Testing the Auth0 Integration

1. Start the application: `python main.py`
2. Visit: http://localhost:8000
3. Call the login endpoint: `GET http://localhost:8000/auth/login`
4. Visit the returned `auth_url` to complete OAuth flow
5. You'll be redirected back with a JWT token

## User Information Fields

Auth0 typically returns user information in this format:
```json
{
  "sub": "auth0|12345",
  "email": "user@example.com", 
  "name": "John Doe",
  "picture": "https://gravatar.com/avatar/...",
  "email_verified": true,
  "updated_at": "2024-01-01T00:00:00.000Z"
}
```

The application extracts: `sub`, `email`, `name`, and `picture` for the JWT token.

## Scopes

The application requests these scopes by default:
- `openid`: Required for OpenID Connect
- `profile`: Access to user profile information
- `email`: Access to user email address

You can modify the scopes in `auth/oauth_client.py` if needed.

## Production Considerations

- Use HTTPS callback URLs in production
- Set proper CORS origins
- Use a secure JWT secret key
- Consider implementing refresh tokens
- Add proper error handling and logging
- Store user data in a database
- Implement proper session management
