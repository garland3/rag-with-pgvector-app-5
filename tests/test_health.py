"""
Test health and basic endpoints.
"""
import pytest


@pytest.mark.api
def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "config" in data
    assert isinstance(data["config"], dict)


@pytest.mark.api  
def test_root_endpoint_unauthenticated(client):
    """Test root endpoint without authentication."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.api
def test_docs_endpoints(client):
    """Test that API documentation endpoints are accessible."""
    # Test OpenAPI/Swagger docs
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test ReDoc
    response = client.get("/redoc") 
    assert response.status_code == 200
    
    # Test OpenAPI spec
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data