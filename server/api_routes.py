from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from server.models import Script, Role, Clue, PlotOutline, Vote, Accusation
from server.game_manager import manager
from server.host_dm import host as host_dm
from server.middleware import require_admin
import uuid

router = APIRouter()

# --- Genre constants ---
GENRES = [
    {"value": "悬疑推理", "label": "经典谋杀案，逻辑推理"},
    {"value": "古风权谋", "label": "古代宫廷/江湖，权力斗争"},
    {"value": "现代都市", "label": "当代社会背景，情感纠葛"},
    {"value": "恐怖惊悚", "label": "超自然元素，心理恐惧"},
    {"value": "欢乐搞笑", "label": "轻松幽默，反转结局"},
    {"value": "科幻未来", "label": "赛博朋克/太空，高科技犯罪"},
]

DIFFICULTIES = ["简单", "中等", "困难"]


# --- Request models ---

class PlayerJoinRequest(BaseModel):
    player_id: str
    name: str


class CreateRoomRequest(BaseModel):
    creator_id: str  # 管理员ID


class ScriptGenerationRequest(BaseModel):
    genre: str
    difficulty: str = "中等"
    estimated_time: int = 90
    player_count: int = 4


class SetScriptRequest(BaseModel):
    script: Script


class AccusationRequest(BaseModel):
    from_player_id: str
    target_role_name: str
    reasoning: str


class VoteRequest(BaseModel):
    from_player_id: str
    target_role_name: str
    reasoning: str


class ChatMessageRequest(BaseModel):
    player_id: str
    message: str
    is_private: bool = False
    target_player_id: Optional[str] = None


class AdminActionRequest(BaseModel):
    player_id: str  # 管理员ID，用于权限校验


class PushEventRequest(BaseModel):
    player_id: str
    event_content: str


class AddClueRequest(BaseModel):
    player_id: str
    clue_title: str
    clue_content: str


class LLMConfigRequest(BaseModel):
    endpoint: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


# --- Room endpoints ---

@router.post("/api/rooms")
async def create_room(req: CreateRoomRequest):
    game_id = str(uuid.uuid4())
    manager.create_game(game_id, req.creator_id)
    return {"game_id": game_id}


@router.get("/api/rooms")
async def list_rooms():
    return [
        {
            "game_id": gid,
            "player_count": sum(1 for pid in state.players if pid != state.room_creator_id),
            "phase": state.phase,
            "act": state.act,
            "script_generated": state.script_generated,
            "title": state.script.title if state.script.title != "待生成" else "",
        }
        for gid, state in manager.games.items()
    ]


@router.get("/api/rooms/{game_id}")
async def get_room(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "game_id": state.game_id,
        "phase": state.phase,
        "act": state.act,
        "room_creator_id": state.room_creator_id,
        "script_generated": state.script_generated,
        "players": {
            pid: {
                "name": p.name,
                "role_id": p.role_id,
                "role_name": p.role.name if p.role else "",
            }
            for pid, p in state.players.items()
        },
        "script": {
            "title": state.script.title,
            "genre": state.script.genre,
            "difficulty": state.script.difficulty,
            "estimated_time": state.script.estimated_time,
            "background_story": state.script.background_story,
            "true_killer": state.script.true_killer,
            "roles": [r.model_dump() for r in state.script.roles],
            "roles_count": len(state.script.roles),
        } if state.script_generated else None,
        "clues": [c.model_dump() for c in state.script.clues],
        "votes": [v.model_dump() for v in state.votes],
        "public_messages": [m.model_dump() for m in state.public_messages[-50:]],  # last 50
    }


@router.delete("/api/rooms/{game_id}")
async def delete_room(game_id: str):
    if game_id in manager.games:
        del manager.games[game_id]
    return {"status": "deleted"}


# --- Player endpoints ---

@router.post("/api/rooms/{game_id}/players")
async def add_player(game_id: str, req: PlayerJoinRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    player = manager.add_player(game_id, req.player_id, req.name)
    if player is None:
        raise HTTPException(status_code=400, detail="房间已满或剧本未生成")
    return {"player_id": player.id, "name": player.name, "role_id": player.role_id}


@router.get("/api/rooms/{game_id}/players")
async def list_players(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        pid: {"name": p.name, "role_id": p.role_id}
        for pid, p in state.players.items()
    }


# --- Script generation endpoints (admin only) ---

@router.post("/api/rooms/{game_id}/generate-script")
async def generate_script(game_id: str, req: ScriptGenerationRequest):
    """触发LLM生成剧本（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != "waiting":
        raise HTTPException(status_code=400, detail="只能在等待阶段生成剧本")

    # Build detailed prompt for LLM
    user_prompt = f"""请生成一个完整的剧本杀剧本，以JSON格式返回。

类型：{req.genre}
难度：{req.difficulty}
预计时长：{req.estimated_time}分钟
玩家数量：{req.player_count}人（需要{req.player_count}个角色）

JSON格式要求：
{{
  "title": "剧本标题",
  "genre": "{req.genre}",
  "difficulty": "{req.difficulty}",
  "estimated_time": {req.estimated_time},
  "background_story": "背景故事（200-500字）",
  "true_killer": "凶手角色名",
  "murder_method": "作案手法描述",
  "cover_up": "掩盖手段描述",
  "roles": [
    {{
      "id": "role_1",
      "name": "角色名",
      "age": 年龄数字,
      "occupation": "职业",
      "description": "简短描述",
      "background": "个人背景故事（100-200字）",
      "secret_task": "秘密任务",
      "alibi": "不在场证明",
      "motive": "作案动机",
      "relationships": []
    }}
  ],
  "clues": [
    {{
      "id": "clue_1",
      "title": "线索标题",
      "content": "线索内容描述",
      "target_role": null,
      "is_red_herring": false,
      "content_hint": "提示"
    }}
  ],
  "plot_outline": {{
    "act1": "第一幕概述（背景介绍）",
    "act2": "第二幕概述（自由调查）",
    "act3": "第三幕概述（审判揭晓）"
  }}
}}

注意：
- 确保有{req.player_count}个角色
- 每个角色的id必须是唯一的（role_1, role_2...）
- 线索数量至少5条
- 凶手必须是其中一个角色"""

    try:
        raw_json = host_dm.generate_script(
            "你是一名剧本杀设计师，请生成完整的剧本。只返回JSON，不要其他内容。",
            user_prompt,
        )
        # Parse JSON from LLM response
        import json
        # Handle markdown code blocks
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0].strip()

        script_dict = json.loads(raw_json)
        script = Script(**script_dict)

        manager.set_script(game_id, script)
        state.script_generated = True

        return {
            "status": "generated",
            "title": script.title,
            "roles_count": len(script.roles),
            "clues_count": len(script.clues),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"剧本生成失败: {str(e)}")


def _generate_script_stream_generator(game_id: str, req: ScriptGenerationRequest):
    """Generator for SSE streaming of script generation."""
    state = manager.get_state(game_id)
    if not state:
        yield f"data: {{\"type\": \"error\", \"message\": \"Room not found\"}}\n\n"
        return
    if state.phase != "waiting":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待阶段生成剧本\"}}\n\n"
        return

    # Build prompt
    user_prompt = f"""请生成一个完整的剧本杀剧本，以JSON格式返回。

类型：{req.genre}
难度：{req.difficulty}
预计时长：{req.estimated_time}分钟
玩家数量：{req.player_count}人（需要{req.player_count}个角色）

JSON格式要求：
{{
  "title": "剧本标题",
  "genre": "{req.genre}",
  "difficulty": "{req.difficulty}",
  "estimated_time": {req.estimated_time},
  "background_story": "背景故事（200-500字）",
  "true_killer": "凶手角色名",
  "murder_method": "作案手法描述",
  "cover_up": "掩盖手段描述",
  "roles": [
    {{
      "id": "role_1",
      "name": "角色名",
      "age": 年龄数字,
      "occupation": "职业",
      "description": "简短描述",
      "background": "个人背景故事（100-200字）",
      "secret_task": "秘密任务",
      "alibi": "不在场证明",
      "motive": "作案动机",
      "relationships": []
    }}
  ],
  "clues": [
    {{
      "id": "clue_1",
      "title": "线索标题",
      "content": "线索内容描述",
      "target_role": null,
      "is_red_herring": false,
      "content_hint": "提示"
    }}
  ],
  "plot_outline": {{
    "act1": "第一幕概述（背景介绍）",
    "act2": "第二幕概述（自由调查）",
    "act3": "第三幕概述（审判揭晓）"
  }}
}}

注意：
- 确保有{req.player_count}个角色
- 每个角色的id必须是唯一的（role_1, role_2...）
- 线索数量至少5条
- 凶手必须是其中一个角色"""

    try:
        # Send start event
        yield f"data: {{\"type\": \"start\"}}\n\n"

        # Stream chunks
        full_text = ""
        for chunk in host_dm.llm.generate_script_stream(
            "你是一名剧本杀设计师，请生成完整的剧本。只返回JSON，不要其他内容。",
            user_prompt,
        ):
            full_text += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        # Parse JSON
        raw_json = full_text
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0].strip()

        script_dict = json.loads(raw_json)
        script = Script(**script_dict)
        manager.set_script(game_id, script)
        state.script_generated = True

        yield f"data: {{\"type\": \"done\", \"title\": {json.dumps(script.title, ensure_ascii=False)}, \"roles_count\": {len(script.roles)}, \"clues_count\": {len(script.clues)}}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/api/rooms/{game_id}/generate-script-stream")
async def generate_script_stream(game_id: str, req: ScriptGenerationRequest):
    """流式生成剧本，通过 SSE 实时返回进度。"""
    return StreamingResponse(
        _generate_script_stream_generator(game_id, req),
        media_type="text/event-stream",
    )


@router.post("/api/rooms/{game_id}/set-script")
async def set_script(game_id: str, req: SetScriptRequest):
    """手动设置剧本（管理员编辑后保存）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != "waiting":
        raise HTTPException(status_code=400, detail="只能在等待阶段设置剧本")

    manager.set_script(game_id, req.script)
    state.script_generated = True
    return {"status": "saved", "title": req.script.title}


@router.get("/api/genres")
async def list_genres():
    """返回可用的剧本类型列表"""
    return {"genres": GENRES, "difficulties": DIFFICULTIES}


# --- Game control endpoints ---

@router.post("/api/rooms/{game_id}/start")
async def start_game(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    playable_count = sum(1 for pid in state.players if pid != state.room_creator_id)
    if playable_count < 2:
        raise HTTPException(status_code=400, detail="至少需要2名玩家才能开始")
    if not state.script_generated:
        raise HTTPException(status_code=400, detail="先生成剧本再开始游戏")
    manager.start_game(game_id)
    return {"game_id": game_id, "phase": state.phase}


# --- Admin emergency controls (admin only) ---

@router.post("/api/rooms/{game_id}/dm/push-event")
async def push_event(game_id: str, req: PushEventRequest):
    """手动推进剧情（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    # Use LLM to generate next event based on current state
    try:
        event_content = host_dm.generate_event(state)
        manager.push_event(game_id, event_content)
        return {"status": "event_pushed", "content": event_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"事件生成失败: {str(e)}")


@router.post("/api/rooms/{game_id}/dm/add-clue")
async def add_clue(game_id: str, req: AddClueRequest):
    """追加自定义线索（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    manager.add_clue(game_id, req.clue_title, req.clue_content)
    # Also push as event message
    manager.push_event(game_id, f"🔍 新线索发现：{req.clue_title} — {req.clue_content}")
    return {"status": "clue_added"}


@router.post("/api/rooms/{game_id}/force-trial")
async def force_trial(game_id: str, req: AdminActionRequest):
    """强制进入审判（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    manager.force_trial(game_id)
    return {"status": "trial_started", "phase": state.phase}


@router.post("/api/rooms/{game_id}/end-game")
async def end_game(game_id: str, req: AdminActionRequest):
    """提前结束游戏（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    # Generate truth reveal via LLM
    try:
        reveal_content = host_dm.generate_event(state)  # reuse for now
        manager.push_event(game_id, f"📢 真相揭晓：{reveal_content}")
    except Exception:
        pass

    manager.end_game(game_id)
    return {"status": "game_ended", "phase": state.phase}


@router.post("/api/rooms/{game_id}/players/{target_pid}/kick")
async def kick_player(game_id: str, target_pid: str, req: AdminActionRequest):
    """踢出玩家（仅管理员）"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    manager.kick_player(game_id, target_pid)
    return {"status": "kicked", "target_player_id": target_pid}


@router.get("/api/rooms/{game_id}/dm/log")
async def get_dm_log(game_id: str):
    """获取DM推理日志"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"dm_log": state.dm_log}


# --- Accusation endpoints ---

@router.post("/api/rooms/{game_id}/accusations")
async def add_accusation(game_id: str, req: AccusationRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    accusation = Accusation(
        from_player_id=req.from_player_id,
        target_role_name=req.target_role_name,
        reasoning=req.reasoning,
    )
    manager.add_accusation(game_id, accusation)
    return {"status": "accusation recorded"}


# --- Voting endpoints ---

@router.post("/api/rooms/{game_id}/votes")
async def add_vote(game_id: str, req: VoteRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    vote = Vote(
        from_player_id=req.from_player_id,
        target_role_name=req.target_role_name,
        reasoning=req.reasoning,
    )
    manager.add_vote(game_id, vote)
    return {"status": "vote recorded"}


@router.get("/api/rooms/{game_id}/consensus")
async def check_consensus(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    reached = manager.check_consensus(game_id)
    return {
        "consensus_reached": reached,
        "votes": [v.model_dump() for v in state.votes],
    }


# --- Chat endpoints ---

@router.post("/api/rooms/{game_id}/chat")
async def send_message(game_id: str, req: ChatMessageRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=400, detail="Player not in room")
    manager.add_chat_message(
        game_id, req.player_id, req.message, req.is_private, req.target_player_id
    )
    return {"status": "message sent"}


# --- LLM config endpoints ---

@router.get("/api/llm-config")
async def get_llm_config():
    """获取当前 LLM 配置（api_key 脱敏）"""
    return host_dm.llm.get_config()


@router.post("/api/llm-config")
async def update_llm_config(req: LLMConfigRequest):
    """更新 LLM 配置（运行时生效，不持久化到 .env）"""
    host_dm.llm.set_runtime_config(
        endpoint=req.endpoint,
        model=req.model,
        api_key=req.api_key,
    )
    return {"status": "updated", **host_dm.llm.get_config()}


@router.post("/api/test-llm")
async def test_llm(req: Optional[LLMConfigRequest] = None):
    """测试 LLM 连接。可传入可选配置进行临时测试（不保存）。"""
    # Save original config for restore
    orig_endpoint = host_dm.llm.endpoint
    orig_model = host_dm.llm.model
    orig_api_key = host_dm.llm.api_key

    if req and (req.endpoint or req.model or req.api_key is not None):
        # Only override fields that user explicitly provided
        endpoint_to_use = _normalize_endpoint(req.endpoint) if req.endpoint else orig_endpoint
        model_to_use = req.model if req.model else orig_model
        api_key_to_use = req.api_key if req.api_key is not None else orig_api_key
        host_dm.llm.set_runtime_config(
            endpoint=endpoint_to_use,
            model=model_to_use,
            api_key=api_key_to_use,
        )

    try:
        import time
        start = time.time()
        result = host_dm.llm.test_connection()
        elapsed = time.time() - start
        return {
            "status": "connected",
            "response_time_ms": round(elapsed * 1000),
            "model": host_dm.llm.model,
            "endpoint": host_dm.llm.endpoint,
            "sample_response": result[:200],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        # Always restore original config after test
        host_dm.llm.set_runtime_config(
            endpoint=orig_endpoint,
            model=orig_model,
            api_key=orig_api_key,
        )


def _normalize_endpoint(url: Optional[str]) -> str:
    """Ensure endpoint has http:// scheme and strip trailing slash."""
    if not url:
        return ""
    url = url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url


@router.get("/api/llm-models")
async def list_llm_models():
    """获取 LLM 提供商可用的模型列表"""
    try:
        models = host_dm.llm.list_models()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@router.get("/api/health")
async def health_check():
    return {"status": "ok", "games_count": len(manager.games)}
