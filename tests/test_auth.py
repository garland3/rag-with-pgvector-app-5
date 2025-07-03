"""
Test authentication endpoints and middleware.
"""
import pytest
from unittest.mock import patch


@pytest.mark.auth
@pytest.mark.api
def test_auth_login_oauth_not_configured(client):
    """Test login endpoint when OAuth is not configured."""
    with patch("routes.auth.oauth_client") as mock_client:
        mock_client.client_id = None
        mock_client.client_secret = None
        
        response = client.get("/auth/login")
        assert response.status_code == 500
        assert "OAuth client not properly configured" in response.json()["detail"]


@pytest.mark.auth
@pytest.mark.api 
def test_auth_login_oauth_configured(client, mock_oauth_settings):
    """Test login endpoint when OAuth is properly configured."""
    with patch("routes.auth.oauth_client") as mock_client, \
         patch("routes.auth._states", {}):
        
        mock_client.client_id = "test-client-id"
        mock_client.client_secret = "test-client-secret"  # nosec B105
        mock_client.get_authorization_url.return_value = ("https://test.auth0.com/authorize?code=test", "test-state")
        
        response = client.get("/auth/login")
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        
        # The endpoint should return a 302 redirect or 200 with auth URL
        assert response.status_code in [200, 302]


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_missing_code(client):
    """Test callback endpoint with missing code parameter."""
    response = client.get("/auth/callback?state=test-state")
    assert response.status_code == 422  # FastAPI validation error for missing required parameter


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_missing_state(client):
    """Test callback endpoint with missing state parameter."""
    response = client.get("/auth/callback?code=test-code")
    assert response.status_code == 422  # FastAPI validation error for missing required parameter


@pytest.mark.auth
@pytest.mark.api
def test_auth_callback_oauth_error(client):
    """Test callback endpoint with OAuth error."""
    response = client.get("/auth/callback?code=test-code&state=test-state&error=access_denied&error_description=User+denied+access")
    assert response.status_code == 400  # Now we have required params, so we get the error handling logic
    assert "access_denied" in response.json()["detail"]


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