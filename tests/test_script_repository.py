import pytest
from server.script_repository import ScriptRepository


def test_init_creates_table():
    """Test that initialization creates the scripts table"""
    repo = ScriptRepository(":memory:")
    cursor = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scripts'")
    assert cursor.fetchone() is not None


def test_init_creates_indexes():
    """Test that initialization creates indexes for genre, difficulty, player_count"""
    repo = ScriptRepository(":memory:")
    
    # Check idx_genre
    cursor = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_genre'")
    assert cursor.fetchone() is not None
    
    # Check idx_difficulty
    cursor = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_difficulty'")
    assert cursor.fetchone() is not None
    
    # Check idx_player_count
    cursor = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_player_count'")
    assert cursor.fetchone() is not None


def test_create_script():
    """Test creating a script and retrieving it"""
    repo = ScriptRepository(":memory:")
    script_data = {
        "title": "Test Script",
        "genre": "悬疑",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "Test story"
    }
    script_id = repo.create(script_data)
    assert script_id is not None
    
    retrieved = repo.get(script_id)
    assert retrieved is not None
    assert retrieved["title"] == "Test Script"
    assert retrieved["genre"] == "悬疑"
    assert retrieved["difficulty"] == "中等"
    assert retrieved["player_count"] == 6


def test_get_nonexistent_script():
    """Test retrieving a script that doesn't exist"""
    repo = ScriptRepository(":memory:")
    result = repo.get("nonexistent-id")
    assert result is None


def test_list_scripts_with_filters():
    """Test listing scripts with various filters"""
    repo = ScriptRepository(":memory:")
    repo.create({"title": "Script 1", "genre": "悬疑", "difficulty": "中等", "player_count": 6})
    repo.create({"title": "Script 2", "genre": "古风", "difficulty": "困难", "player_count": 8})
    repo.create({"title": "Script 3", "genre": "悬疑", "difficulty": "简单", "player_count": 4})
    
    # Filter by genre
    scripts = repo.list_scripts(genre="悬疑")
    assert len(scripts) == 2
    
    # Filter by difficulty
    scripts = repo.list_scripts(difficulty="中等")
    assert len(scripts) == 1
    assert scripts[0]["title"] == "Script 1"
    
    # Filter by min_players
    scripts = repo.list_scripts(min_players=6)
    assert len(scripts) == 2
    
    # Combined filters
    scripts = repo.list_scripts(genre="悬疑", min_players=5)
    assert len(scripts) == 1
    assert scripts[0]["title"] == "Script 1"


def test_soft_delete():
    """Test soft delete marks script as inactive"""
    repo = ScriptRepository(":memory:")
    script_id = repo.create({"title": "To Delete", "genre": "悬疑"})
    
    result = repo.soft_delete(script_id)
    assert result is True
    
    retrieved = repo.get(script_id)
    assert retrieved is None  # Should not return soft-deleted scripts


def test_soft_delete_nonexistent():
    """Test soft delete on nonexistent script returns False"""
    repo = ScriptRepository(":memory:")
    result = repo.soft_delete("nonexistent-id")
    assert result is False


def test_export_all():
    """Test exporting all active scripts"""
    repo = ScriptRepository(":memory:")
    script_data = {"title": "Export Test", "genre": "悬疑", "difficulty": "中等"}
    script_id = repo.create(script_data)
    
    exported = repo.export_all()
    assert len(exported) == 1
    assert exported[0]["title"] == "Export Test"


def test_import_scripts():
    """Test importing scripts"""
    repo = ScriptRepository(":memory:")
    scripts = [
        {"title": "Import 1", "genre": "悬疑"},
        {"title": "Import 2", "genre": "古风"}
    ]
    count = repo.import_scripts(scripts)
    assert count == 2
    
    all_scripts = repo.list_scripts()
    assert len(all_scripts) == 2


def test_export_import_roundtrip():
    """Test export and import roundtrip"""
    repo1 = ScriptRepository(":memory:")
    script_data = {"title": "Roundtrip Test", "genre": "悬疑", "difficulty": "中等"}
    script_id = repo1.create(script_data)
    
    exported = repo1.export_all()
    assert len(exported) == 1
    
    repo2 = ScriptRepository(":memory:")
    count = repo2.import_scripts(exported)
    assert count == 1
    
    scripts = repo2.list_scripts()
    assert len(scripts) == 1
    assert scripts[0]["title"] == "Roundtrip Test"


def test_full_content_json_serialization():
    """Test that full_content is properly JSON serialized"""
    repo = ScriptRepository(":memory:")
    script_data = {
        "title": "JSON Test",
        "genre": "悬疑",
        "complex_field": {"nested": {"data": [1, 2, 3]}}
    }
    script_id = repo.create(script_data)
    
    retrieved = repo.get(script_id)
    assert retrieved is not None
    # full_content should be a dict after JSON deserialization
    assert isinstance(retrieved["full_content"], dict)
    assert retrieved["full_content"]["complex_field"]["nested"]["data"] == [1, 2, 3]
