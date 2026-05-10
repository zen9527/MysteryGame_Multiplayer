import pytest
from server.script_service import ScriptService
from server.script_repository import ScriptRepository


@pytest.fixture
def service():
    repo = ScriptRepository(":memory:")
    return ScriptService(repo)


def test_list_scripts_returns_metadata_only(service):
    """Test that list_scripts returns metadata without sensitive fields"""
    script_data = {
        "title": "Test Script",
        "genre": "悬疑",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "Test story",
        "true_killer": "角色 A",
        "roles": [],
        "clues": [{"title": "Secret Clue"}]
    }
    service.upload(script_data)
    
    scripts = service.list_scripts()
    assert len(scripts) == 1
    assert "true_killer" not in scripts[0]
    assert "clues" not in scripts[0]


def test_get_detail_masks_sensitive_fields(service):
    """Test that get_detail masks true_killer, murder_method, clues"""
    script_data = {
        "title": "Detail Test",
        "genre": "悬疑",
        "true_killer": "角色 A",
        "murder_method": "毒药",
        "roles": [{"id": "1", "name": "角色 A", "age": 30, "occupation": "医生", 
                   "description": "描述", "background": "背景", "secret_task": "任务", "alibi": "不在场证明"}],
        "clues": [{"title": "Secret"}],
        "plot_outline": {"act1": "第一幕", "act2": "第二幕", "act3": "第三幕"}
    }
    service.upload(script_data)
    
    scripts = service.list_scripts()
    detail = service.get_detail(scripts[0]["id"])
    
    assert "true_killer" not in detail
    assert "murder_method" not in detail
    assert "clues" not in detail
    assert "private_events" not in detail
    assert "roles" in detail
    assert "plot_outline" in detail


def test_upload_and_delete(service):
    """Test upload and delete operations"""
    script_data = {"title": "Delete Test", "genre": "悬疑"}
    script_id = service.upload(script_data)
    
    scripts_before = service.list_scripts()
    assert len(scripts_before) == 1
    
    result = service.delete(script_id)
    assert result is True
    
    scripts_after = service.list_scripts()
    assert len(scripts_after) == 0


def test_export_and_import(service):
    """Test export and import operations"""
    script_data = {"title": "Export Test", "genre": "悬疑"}
    service.upload(script_data)
    
    exported = service.export_all()
    assert len(exported) == 1
    
    # Create new service with fresh repo
    new_repo = ScriptRepository(":memory:")
    new_service = ScriptService(new_repo)
    
    count = new_service.import_scripts(exported)
    assert count == 1
    
    scripts = new_service.list_scripts()
    assert len(scripts) == 1
    assert scripts[0]["title"] == "Export Test"


def test_get_detail_not_found(service):
    """Test get_detail returns None for non-existent script"""
    result = service.get_detail("non-existent-id")
    assert result is None
