import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.di import container

client = TestClient(app)
ADMIN_KEY = "admin_secret_key"


def _get_service():
    return container.resolve("script_service")


def test_get_scripts_public():
    """Test public script listing endpoint"""
    response = client.get("/api/scripts")
    assert response.status_code == 200
    assert "scripts" in response.json()


def test_get_script_detail():
    """Test script detail endpoint with masked sensitive fields"""
    # First upload a script
    script_data = {
        "title": "Detail Test",
        "genre": "悬疑",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "Test",
        "true_killer": "角色 A",
        "murder_method": "测试",
        "cover_up": "测试",
        "roles": [{"id": "1", "name": "角色 A", "age": 30, "occupation": "测试", 
                   "description": "描述", "background": "背景", "secret_task": "任务", "alibi": "不在场证明"}],
        "clues": [],
        "plot_outline": {"act1": "第一幕", "act2": "第二幕", "act3": "第三幕"}
    }
    
    response = client.post("/api/scripts", json=script_data, params={"admin_key": ADMIN_KEY})
    assert response.status_code == 200
    script_id = response.json()["script_id"]
    
    # Get detail (should be masked)
    response = client.get(f"/api/scripts/{script_id}")
    assert response.status_code == 200
    data = response.json()
    assert "true_killer" not in data
    assert "murder_method" not in data
    assert "clues" not in data


def test_upload_script_requires_admin():
    """Test that upload script requires admin authentication"""
    script_data = {
        "title": "Test", 
        "genre": "悬疑", 
        "true_killer": "角色 A", 
        "murder_method": "测试", 
        "cover_up": "测试", 
        "roles": [], 
        "clues": [], 
        "plot_outline": {}
    }
    
    # Without admin key - should fail (422 for missing required param, or 403 for invalid key)
    response = client.post("/api/scripts", json=script_data)
    assert response.status_code == 422 or response.status_code == 403
    
    # With invalid admin key - should fail with 403
    response = client.post("/api/scripts", json=script_data, params={"admin_key": "wrong_key"})
    assert response.status_code == 403


def test_delete_script():
    """Test delete script endpoint"""
    # Upload first
    script_data = {
        "title": "Delete Test", 
        "genre": "悬疑", 
        "true_killer": "角色 A", 
        "murder_method": "测试", 
        "cover_up": "测试", 
        "roles": [], 
        "clues": [], 
        "plot_outline": {}
    }
    
    response = client.post("/api/scripts", json=script_data, params={"admin_key": ADMIN_KEY})
    script_id = response.json()["script_id"]
    
    # Delete
    response = client.delete(f"/api/scripts/{script_id}", params={"admin_key": ADMIN_KEY})
    assert response.status_code == 200
    
    # Verify deleted (should return 404)
    response = client.get(f"/api/scripts/{script_id}")
    assert response.status_code == 404


def test_export_scripts():
    """Test export all scripts endpoint"""
    response = client.get("/api/scripts/export", params={"admin_key": ADMIN_KEY})
    assert response.status_code == 200
    assert "scripts" in response.json()


def test_import_scripts():
    """Test import scripts endpoint"""
    scripts_data = {
        "scripts": [
            {"title": "Imported 1", "genre": "悬疑", "difficulty": "中等"},
            {"title": "Imported 2", "genre": "古风", "difficulty": "困难"}
        ]
    }
    
    response = client.post("/api/scripts/import", json=scripts_data, params={"admin_key": ADMIN_KEY})
    assert response.status_code == 200
    assert response.json()["imported"] == 2
