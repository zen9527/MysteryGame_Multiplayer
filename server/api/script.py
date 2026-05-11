from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
from server.di import container
from server.middleware import require_admin

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


class ScriptGenerationRequest(BaseModel):
    genre: str
    difficulty: str = "中等"
    estimated_time: int = 90
    player_count: int = 4


class SetScriptRequest(BaseModel):
    """Full script JSON for manual set (admin edited content)."""
    title: str
    genre: str = "悬疑推理"
    difficulty: str = "中等"
    estimated_time: int = 90
    background_story: str = ""
    true_killer: str = ""
    murder_method: str = ""
    cover_up: str = ""
    roles: list = []
    clues: list = []
    plot_outline: dict = {}
    private_events: list = []


def _generate_script_generator(game_id: str, req: ScriptGenerationRequest):
    """Generator for SSE streaming of script generation."""
    state = _get_manager().get_state(game_id)
    if not state:
        yield f"data: {{\"type\": \"error\", \"message\": \"Room not found\"}}\n\n"
        return
    if state.phase != "waiting":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待阶段生成剧本\"}}\n\n"

    from server.script_engine.models import ScriptV2
    script_gen = container.resolve("script_generator")

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_text = ""
        for chunk in script_gen.generate_stream(req.genre, req.difficulty, req.player_count, req.estimated_time):
            full_text += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        script_dict = script_gen.normalize_script_json(full_text)
        script = ScriptV2(**script_dict)
        _get_manager().set_script(game_id, script)
        state.script_generated = True

        yield f"data: {{\"type\": \"done\", \"title\": {json.dumps(script.title, ensure_ascii=False)}, \"roles_count\": {len(script.roles)}, \"clues_count\": {len(script.clues)}}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/rooms/{game_id}/generate-script")
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


@router.post("/rooms/{game_id}/set-script")
async def set_script(game_id: str, req: SetScriptRequest):
    """手动设置剧本（管理员编辑后保存）"""
    from server.script_engine.models import ScriptV2
    from server.script_engine.generator import ScriptGenerator

    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != "waiting":
        raise HTTPException(status_code=400, detail="只能在等待阶段设置剧本")

    script_data = req.model_dump()
    # Normalize via ScriptGenerator (reuse logic)
    script_gen = container.resolve("script_generator")
    script_data = script_gen.normalize_script_json(json.dumps(script_data))
    script = ScriptV2(**script_data)
    _get_manager().set_script(game_id, script)
    state.script_generated = True

    hub = container.resolve("websocket_hub")
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

    return {"status": "saved", "title": script.title}
