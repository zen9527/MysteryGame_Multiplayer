import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_endpoint_skips_validation():
    """Health endpoints should bypass validation."""
    response = client.get("/health")
    # Health endpoint may not exist, but should not fail with 400 validation error
    assert response.status_code in [200, 404]


def test_post_requires_json_content_type():
    """POST requests to /api/ should require JSON content type."""
    response = client.post('/api/rooms', data={})
    # Should fail with 400 (validation error) or 422 (FastAPI validation)
    assert response.status_code in [400, 422]


def test_post_with_json_content_type():
    """POST requests with JSON content type should work."""
    response = client.post(
        '/api/rooms',
        json={"name": "Test Room", "creator_id": "player1"}
    )
    # Should succeed or fail with business logic error, not validation error
    assert response.status_code != 400


def test_get_with_query_params():
    """GET requests with query params should work."""
    response = client.get('/api/scripts?genre=悬疑推理')
    assert response.status_code == 200


def test_put_requires_json_content_type():
    """PUT requests should require JSON content type."""
    response = client.put('/api/rooms/test', data={})
    assert response.status_code in [400, 422]
