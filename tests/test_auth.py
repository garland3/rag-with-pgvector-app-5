"""
Test authentication endpoints and middleware.
"""
import pytest
from unittest.mock import patch


@pytest.mark.auth
@pytest.mark.api
def test_auth_login_oauth_not_configured(client):
    """Test login endpoint when OAuth is not configured."""
    with patch("auth.oauth_client.oauth_client") as mock_client:
        mock_client.client_id = None
        mock_client.client_secret = None
        
        response = client.get("/auth/login")
        assert response.status_code == 500
        assert "OAuth client not properly configured" in response.json()["detail"]


@pytest.mark.auth
@pytest.mark.api 
def test_auth_login_oauth_configured(client, mock_oauth_settings):
    """Test login endpoint when OAuth is properly configured."""
    with patch("auth.oauth_client.oauth_client") as mock_client:
        mock_client.client_id = "test-client-id"
        mock_client.client_secret = "test-client-secret"
        mock_client.get_authorization_url.return_value = ("https://test.auth0.com/authorize?...", "test-state")
        
        response = client.get("/auth/login")
        assert response.status_code == 302
        assert response.headers["location"].startswith("https://test.auth0.com/authorize")


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_missing_code(client):
    """Test callback endpoint with missing code parameter."""
    response = client.get("/auth/callback?state=test-state")
    assert response.status_code == 400
    assert "Missing code or state parameter" in response.text


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_missing_state(client):
    """Test callback endpoint with missing state parameter."""
    response = client.get("/auth/callback?code=test-code")
    assert response.status_code == 400
    assert "Missing code or state parameter" in response.text


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_oauth_error(client):
    """Test callback endpoint with OAuth error."""
    response = client.get("/auth/callback?error=access_denied&error_description=User+denied+access")
    assert response.status_code == 200
    assert "Authentication Error" in response.text
    assert "access_denied" in response.text


@pytest.mark.auth
@pytest.mark.api
def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.api
def test_protected_endpoint_with_auth(client, auth_headers, authenticated_user):
    """Test accessing protected endpoint with valid authentication."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == authenticated_user.email
    assert data["name"] == authenticated_user.name


@pytest.mark.auth
@pytest.mark.api
def test_auth_token_validation(client):
    """Test token validation with invalid token."""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401