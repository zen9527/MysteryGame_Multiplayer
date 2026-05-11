import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_room_with_creator():
    response = client.post("/api/rooms", json={"creator_id": "admin_1"})
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data


def test_list_rooms():
    client.post("/api/rooms", json={"creator_id": "admin_1"})
    response = client.get("/api/rooms")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_room_not_found():
    response = client.get("/api/rooms/nonexistent")
    assert response.status_code == 404


def test_genres_endpoint():
    response = client.get("/api/genres")
    assert response.status_code == 200
    data = response.json()
    assert len(data["genres"]) == 6
    assert "悬疑推理" in [g["value"] for g in data["genres"]]


def test_start_without_script_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    # Add a player first so we hit the script check, not the player count check
    from server.game_manager import manager
    state = manager.get_state(game_id)
    # Need at least 2 players and no script generated
    from server.models import Role
    state.script.roles = [
        Role(id="1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    manager.add_player(game_id, "p1", "张三")
    manager.add_player(game_id, "p2", "李四")

    response = client.post(f"/api/rooms/{game_id}/start")
    assert response.status_code == 400
    assert "剧本" in response.json()["detail"]


def test_admin_kick_non_admin_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    response = client.post(
        f"/api/rooms/{game_id}/players/p_fake/kick",
        json={"player_id": "not_admin"},
    )
    assert response.status_code == 403


def test_force_trial_by_admin():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    # Start first (need to set script_generated)
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "admin_1"},
    )
    assert response.status_code == 200
    assert response.json()["phase"] == "trial"


def test_force_trial_by_non_admin_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "not_admin"},
    )
    assert response.status_code == 403


def test_end_game_by_admin(monkeypatch):
    # Mock LLM to avoid real API calls in integration tests
    monkeypatch.setattr(
        "server.host_dm.host.generate_event",
        lambda state: {"public_event": "真相揭晓", "private_clues": [], "dm_instruction": ""},
    )

    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/end-game",
        json={"player_id": "admin_1"},
    )
    assert response.status_code == 200
    # SSE response — verify it's a stream
    assert "text/event-stream" in response.headers.get("content-type", "")


def test_dm_log_endpoint():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]

    response = client.get(f"/api/rooms/{game_id}/dm/log")
    assert response.status_code == 200
    assert "dm_log" in response.json()


def test_script_upload_list_detail_flow():
    """Test complete script flow: upload → list → detail → create room"""
    # Step 1: Upload a script (admin action)
    script_data = {
        "title": "Integration Test Script",
        "genre": "悬疑推理",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "这是一个用于集成测试的剧本背景故事。在一个豪华庄园里，发生了一起神秘谋杀案...",
        "true_killer": "角色 A",
        "murder_method": "毒药",
        "cover_up": "伪装成意外",
        "roles": [
            {
                "id": "1",
                "name": "角色 A",
                "age": 35,
                "occupation": "商人",
                "description": "富有的商人，与死者有商业纠纷",
                "background": "背景故事 A",
                "secret_task": "秘密任务 A",
                "alibi": "不在场证明 A",
                "motive": "商业纠纷"
            },
            {
                "id": "2",
                "name": "角色 B",
                "age": 28,
                "occupation": "医生",
                "description": "庄园的私人医生",
                "background": "背景故事 B",
                "secret_task": "秘密任务 B",
                "alibi": "不在场证明 B",
                "motive": "医疗纠纷"
            }
        ],
        "clues": [
            {
                "id": "1",
                "title": "毒药瓶",
                "content": "在死者房间发现一个空毒药瓶",
                "target_role": "角色 A",
                "is_red_herring": False,
                "content_hint": "与商人有关",
                "unlock_phase": "act1"
            }
        ],
        "plot_outline": {
            "act1": "第一幕：发现尸体，初步调查",
            "act2": "第二幕：深入调查，揭露秘密",
            "act3": "第三幕：指认凶手，真相大白"
        },
        "private_events": []
    }

    response = client.post("/api/scripts", json=script_data, params={"admin_key": "admin_secret_key"})
    assert response.status_code == 200, f"Upload failed: {response.text}"
    script_id = response.json()["script_id"]

    # Step 2: List scripts (public endpoint)
    response = client.get("/api/scripts")
    assert response.status_code == 200
    scripts = response.json()["scripts"]
    assert any(s["id"] == script_id for s in scripts)

    # Verify metadata only (no sensitive fields)
    script_metadata = next(s for s in scripts if s["id"] == script_id)
    assert "true_killer" not in script_metadata
    assert "clues" not in script_metadata
    assert "murder_method" not in script_metadata

    # Step 3: Get detail (public endpoint, masked)
    response = client.get(f"/api/scripts/{script_id}")
    assert response.status_code == 200
    detail = response.json()

    assert detail["title"] == "Integration Test Script"
    assert detail["genre"] == "悬疑推理"
    assert len(detail["roles"]) == 2
    assert "plot_outline" in detail

    # Verify sensitive fields are masked
    assert "true_killer" not in detail
    assert "murder_method" not in detail
    assert "clues" not in detail
    assert "private_events" not in detail

    # Step 4: Create room with script (public endpoint)
    response = client.post("/api/rooms", json={
        "name": "Test Admin",
        "creator_id": "admin-1",
        "script_id": script_id
    })
    assert response.status_code == 200
    game_id = response.json()["game_id"]

    # Step 5: Verify room was created with correct script
    response = client.get(f"/api/rooms/{game_id}")
    assert response.status_code == 200
    room = response.json()

    assert room["script"]["title"] == "Integration Test Script"
    assert room["script_generated"] == True

    # Step 6: Verify script can be filtered
    response = client.get("/api/scripts?genre=悬疑推理")
    assert response.status_code == 200
    filtered_scripts = response.json()["scripts"]
    assert any(s["id"] == script_id for s in filtered_scripts)

    response = client.get("/api/scripts?difficulty=中等")
    assert response.status_code == 200
    filtered_scripts = response.json()["scripts"]
    assert any(s["id"] == script_id for s in filtered_scripts)

    # Step 7: Test soft delete
    response = client.delete(f"/api/scripts/{script_id}", params={"admin_key": "admin_secret_key"})
    assert response.status_code == 200

    # Verify script is no longer listed
    response = client.get("/api/scripts")
    scripts = response.json()["scripts"]
    assert not any(s["id"] == script_id for s in scripts)

    # Verify script cannot be retrieved
    response = client.get(f"/api/scripts/{script_id}")
    assert response.status_code == 404


def test_export_import_roundtrip():
    """Test export and import functionality"""
    # Upload a script
    script_data = {
        "title": "Export Test",
        "genre": "古风权谋",
        "difficulty": "困难",
        "player_count": 8,
        "estimated_time": 150,
        "background_story": "Test",
        "true_killer": "角色 A",
        "murder_method": "测试",
        "cover_up": "测试",
        "roles": [{"id": "1", "name": "角色 A", "age": 30, "occupation": "测试", 
                   "description": "描述", "background": "背景", "secret_task": "任务", "alibi": "不在场证明", "motive": "动机"}],
        "clues": [],
        "plot_outline": {"act1": "第一幕", "act2": "第二幕", "act3": "第三幕"}
    }

    response = client.post("/api/scripts", json=script_data, params={"admin_key": "admin_secret_key"})
    script_id = response.json()["script_id"]

    # Export all scripts
    response = client.get("/api/scripts/export", params={"admin_key": "admin_secret_key"})
    assert response.status_code == 200
    exported = response.json()["scripts"]
    assert len(exported) >= 1

    # Delete the script
    client.delete(f"/api/scripts/{script_id}", params={"admin_key": "admin_secret_key"})

    # Import back
    response = client.post("/api/scripts/import", json={"scripts": exported}, params={"admin_key": "admin_secret_key"})
    assert response.status_code == 200
    assert response.json()["imported"] >= 1

    # Verify script is back
    response = client.get("/api/scripts")
    scripts = response.json()["scripts"]
    assert any(s["title"] == "Export Test" for s in scripts)
