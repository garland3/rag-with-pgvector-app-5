"""
Test project management endpoints.
"""
import pytest
from uuid import uuid4


@pytest.mark.api
def test_create_project_unauthenticated(client, sample_project_data):
    """Test creating project without authentication."""
    response = client.post("/projects/", json=sample_project_data)
    assert response.status_code == 401


@pytest.mark.api
def test_create_project_authenticated(client, auth_headers, authenticated_user, sample_project_data):
    """Test creating project with authentication."""
    response = client.post("/projects/", json=sample_project_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == sample_project_data["name"]
    assert data["description"] == sample_project_data["description"]
    assert data["owner_id"] == str(authenticated_user.id)
    assert "id" in data
    assert "created_at" in data


@pytest.mark.api
def test_create_project_form_submission(client, authenticated_user):
    """Test creating project via HTML form submission."""
    # Mock authentication by setting cookie
    with client as test_client:
        # Set auth cookie
        from auth.token_manager import token_manager
        token = token_manager.create_access_token(data={"sub": authenticated_user.auth0_id})
        test_client.cookies.set("access_token", token)
        
        form_data = {
            "name": "Form Test Project",
            "description": "Created via form submission"
        }
        response = test_client.post("/projects/create", data=form_data)
        assert response.status_code == 302  # Redirect
        assert response.headers["location"] == "/"


@pytest.mark.api
def test_get_projects_unauthenticated(client):
    """Test getting projects without authentication."""
    response = client.get("/projects/")
    assert response.status_code == 401


@pytest.mark.api
def test_get_projects_authenticated_empty(client, auth_headers, authenticated_user):
    """Test getting projects with authentication but no projects."""
    response = client.get("/projects/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.api
def test_get_projects_authenticated_with_projects(client, auth_headers, authenticated_user, db_session):
    """Test getting projects with authentication and existing projects."""
    # Create a project first
    from models.project import Project
    from datetime import datetime
    
    project = Project(
        id=uuid4(),
        name="Test Project",
        description="Test Description",
        owner_id=authenticated_user.id,
        created_at=datetime.utcnow()
    )
    db_session.add(project)
    db_session.commit()
    
    response = client.get("/projects/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Project"
    assert data[0]["description"] == "Test Description"
    assert data[0]["owner_id"] == str(authenticated_user.id)


@pytest.mark.api
def test_create_project_validation_missing_name(client, auth_headers):
    """Test creating project with missing name."""
    invalid_data = {"description": "Missing name"}
    response = client.post("/projects/", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.api
def test_create_project_validation_missing_description(client, auth_headers):
    """Test creating project with missing description."""
    invalid_data = {"name": "Missing description"}
    response = client.post("/projects/", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.api
def test_create_project_validation_empty_strings(client, auth_headers):
    """Test creating project with empty strings."""
    invalid_data = {"name": "", "description": ""}
    response = client.post("/projects/", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error