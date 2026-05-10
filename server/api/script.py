from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
from server.models import Script
from server.di import container
from server.middleware import require_admin

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_host_dm():
    return container.resolve("host_dm")


class ScriptGenerationRequest(BaseModel):
    genre: str
    difficulty: str = "中等"
    estimated_time: int = 90
    player_count: int = 4


def _normalize_script_json(data: dict) -> dict:
    """Normalize LLM-generated script JSON to match Pydantic schema."""
    roles = data.get("roles", [])
    for role in roles:
        rels = role.get("relationships", [])
        normalized = []
        for r in rels:
            if isinstance(r, dict):
                normalized.append(r)
            elif isinstance(r, str):
                normalized.append({"target": r, "description": r})
        role["relationships"] = normalized

    clues = data.get("clues", [])
    for clue in clues:
        clue.setdefault("target_player_ids", [])
        clue.setdefault("unlock_phase", "act1")
        clue.setdefault("trigger_condition", None)

    private_events = data.get("private_events", [])
    for event in private_events:
        event.setdefault("trigger", None)

    return data


def _generate_script_generator(game_id: str, req: ScriptGenerationRequest):
    """Generator for SSE streaming of script generation."""
    state = _get_manager().get_state(game_id)
    if not state:
        yield f"data: {{\"type\": \"error\", \"message\": \"Room not found\"}}\n\n"
        return
    if state.phase != "waiting":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待阶段生成剧本\"}}\n\n"

    user_prompt = f"""请生成一个完整的剧本杀剧本，以 JSON 格式返回。

类型：{req.genre}
难度：{req.difficulty}
预计时长：{req.estimated_time}分钟
玩家数量：{req.player_count}人（需要{req.player_count}个角色）

JSON 格式要求：
{{
  "title": "剧本标题",
  "genre": "{req.genre}",
  "difficulty": "{req.difficulty}",
  "estimated_time": {req.estimated_time},
  "background_story": "背景故事（200-500 字）",
  "true_killer": "凶手角色名",
  "murder_method": "作案手法描述",
  "cover_up": "掩盖手段描述",
  "roles": [
    {{
      "id": "role_1",
      "name": "角色名",
      "age": 年龄数字，
      "occupation": "职业",
      "description": "简短描述",
      "background": "个人背景故事（100-200 字）",
      "secret_task": "秘密任务",
      "alibi": "不在场证明",
      "motive": "作案动机",
      "relationships": [
        {{"target": "角色名", "description": "关系描述"}}
      ]
    }}
  ],
  "clues": [
    {{
      "id": "clue_1",
      "title": "线索标题",
      "content": "线索内容描述",
      "target_role": null,
      "is_red_herring": false,
      "content_hint": "提示",
      "target_player_ids": ["角色名"],
      "unlock_phase": "act2",
      "trigger_condition": null
    }}
  ],
  "plot_outline": {{
    "act1": "第一幕概述（背景介绍）",
    "act2": "第二幕概述（自由调查）",
    "act3": "第三幕概述（审判揭晓）"
  }},
  "private_events": [
    {{
      "phase": "act2",
      "target_role_name": "角色名",
      "content": "DM 私信内容",
      "trigger": null
    }}
  ]
}}

注意：
- 确保有{req.player_count}个角色
- 每个角色的 id 必须是唯一的（role_1, role_2...）
- 线索数量至少 5 条
- 凶手必须是其中一个角色
- 每条线索标注 target_player_ids（分配给哪些角色名），unlock_phase（act1/act2/act3）
- 线索的 unlock_phase 必须分散在 act1（2-3 条初始线索）和 act2（3-5 条深入线索）中
- 生成 2-3 个 DM 私信触发点（private_events），分配给不同角色，phase 为 act2
- target_player_ids 使用角色名（如"角色名"），后端会匹配到对应的玩家"""

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_text = ""
        for chunk in _get_host_dm().llm.generate_script_stream(
            "你是一名剧本杀设计师，请生成完整的剧本。只返回 JSON，不要其他内容。",
            user_prompt,
        ):
            full_text += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        raw_json = full_text
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0].strip()

        script_dict = json.loads(raw_json)
        script_dict = _normalize_script_json(script_dict)
        script = Script(**script_dict)
        _get_manager().set_script(game_id, script)
        state.script_generated = True

        yield f"data: {{\"type\": \"done\", \"title\": {json.dumps(script.title, ensure_ascii=False)}, \"roles_count\": {len(script.roles)}, \"clues_count\": {len(script.clues)}}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/api/rooms/{game_id}/generate-script")
async def generate_script(game_id: str, req: ScriptGenerationRequest):
    """流式生成剧本，通过 SSE 实时返回进度。"""
    return StreamingResponse(
        _generate_script_generator(game_id, req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/rooms/{game_id}/set-script")
async def set_script(game_id: str, req: ScriptGenerationRequest):
    """手动设置剧本（管理员编辑后保存）"""
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != "waiting":
        raise HTTPException(status_code=400, detail="只能在等待阶段设置剧本")

    _get_manager().set_script(game_id, req)
    state.script_generated = True

    for pid, player in state.players.items():
        if player.role and pid not in state.distributed_role_cards:
            state.distributed_role_cards[pid] = []
            state.distributed_role_cards[pid].append({
                "type": "role_card",
                "layer": "1",
                "player_id": pid,
                "data": {
                    "name": player.role.name,
                    "description": player.role.description,
                },
            })

    for pid, player in state.players.items():
        if player.role:
            await hub.send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "1",
                "player_id": pid,
                "data": {
                    "name": player.role.name,
                    "description": player.role.description,
                },
            })

    return {"status": "saved", "title": req.title}
