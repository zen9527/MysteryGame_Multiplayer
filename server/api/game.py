from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from server.models import Script, Role, Clue, PlotOutline
from server.di import container
from server.middleware import require_admin
from server.utils.validation import AdminActionRequest
from server.constants import ACT_UNLOCK_MAP

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_host_dm():
    return container.resolve("host_dm")


def _get_hub():
    return container.resolve("websocket_hub")


@router.post("/rooms/{game_id}/start")
async def start_game(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    playable_count = len(state.players)
    if playable_count < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 名玩家才能开始")
    if not state.script_generated:
        raise HTTPException(status_code=400, detail="先生成剧本再开始游戏")
    _get_manager().start_game(game_id)

    unlock_result = _get_manager().unlock_phase(game_id, "playing", 1)

    for pid, player in state.players.items():
        if player.role:
            if pid not in state.distributed_role_cards:
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

    await _get_hub().broadcast(game_id, {
        "type": "phase_unlock",
        "phase": "playing",
        "act": 1,
    })

    for pid, player in state.players.items():
        if player.role:
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "1",
                "player_id": pid,
                "data": {
                    "name": player.role.name,
                    "description": player.role.description,
                },
            })

    if unlock_result:
        for pid, card_data in unlock_result["role_cards"].items():
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "2",
                "player_id": pid,
                "data": card_data,
            })

        for pid, clue_list in unlock_result["clues"].items():
            for clue_data in clue_list:
                await _get_hub().send_to_player(game_id, pid, {
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        for pid, content in unlock_result["private_events"]:
            await _get_hub().send_dm_private(game_id, pid, content)

    asyncio.create_task(_auto_generate_opening(game_id))

    return {"game_id": game_id, "phase": state.phase}


async def _auto_generate_opening(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state or state.phase != "playing":
        return
    try:
        event = await asyncio.to_thread(_get_host_dm().generate_event, state)
        result = _get_manager().push_structured_event(game_id, event)
        if result:
            if result["public_event"]:
                await _get_hub().broadcast(game_id, {
                    "type": "event",
                    "content": result["public_event"],
                })
            for clue in result["private_clues"]:
                await _get_hub().send_dm_private(game_id, clue["player_id"], clue["content"])
    except Exception as e:
        _get_manager().add_dm_log(game_id, f"开场白生成失败：{e}")


def _push_event_generator(game_id: str, state):
    if state.phase != "playing":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在游戏进行中推进剧情\"}}\n\n"
        return

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        event = _get_host_dm().generate_event(state)
        state.current_round += 1
        result = _get_manager().push_structured_event(game_id, event)

        done_payload = json.dumps({
            "type": "done",
            "public_event": result["public_event"] if result else "",
            "private_clues_count": len(result["private_clues"]) if result else 0,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/rooms/{game_id}/dm/push-event")
async def push_event(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    return StreamingResponse(
        _push_event_generator(game_id, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/rooms/{game_id}/advance-act")
async def advance_act(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    if state.phase not in ("playing",):
        raise HTTPException(status_code=400, detail="只能在游戏进行中推进幕")

    new_act = state.act + 1
    if new_act > 3:
        raise HTTPException(status_code=400, detail="已经是最后一幕，无法继续推进")

    unlock_result = _get_manager().unlock_phase(game_id, "playing", new_act)

    await _get_hub().broadcast(game_id, {
        "type": "phase_unlock",
        "phase": "playing",
        "act": new_act,
    })

    plot_text = ""
    act_key = f"act{new_act}"
    if hasattr(state.script, 'plot_outline') and state.script.plot_outline:
        plot_text = getattr(state.script.plot_outline, act_key, "")
    await _get_hub().broadcast(game_id, {
        "type": "act_transition",
        "act": new_act,
        "plot_summary": plot_text,
    })

    if unlock_result:
        act_key = f"act{new_act}"
        layer_to_unlock = ACT_UNLOCK_MAP.get(act_key, "2")

        for pid, card_data in unlock_result["role_cards"].items():
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": layer_to_unlock,
                "player_id": pid,
                "data": card_data,
            })

        for pid, clue_list in unlock_result["clues"].items():
            for clue_data in clue_list:
                await _get_hub().send_to_player(game_id, pid, {
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        for pid, content in unlock_result["private_events"]:
            await _get_hub().send_dm_private(game_id, pid, content)

    return {"status": "act_advanced", "act": new_act}


@router.post("/rooms/{game_id}/force-trial")
async def force_trial(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().force_trial(game_id)
    return {"status": "trial_started", "phase": state.phase}


def _end_game_generator(game_id: str, state):
    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        reveal_result = _get_host_dm().generate_event(state)
        reveal_text = reveal_result.get("public_event", str(reveal_result)) if isinstance(reveal_result, dict) else str(reveal_result)
        _get_manager().push_event(game_id, f"📢 真相揭晓：{reveal_text}")

        if isinstance(reveal_result, dict) and reveal_result.get("private_clues"):
            _get_manager().push_structured_event(game_id, reveal_result)

        done_payload = json.dumps({
            "type": "done",
            "content": reveal_text,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"
    finally:
        _get_manager().end_game(game_id)


@router.post("/rooms/{game_id}/end-game")
async def end_game(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    return StreamingResponse(
        _end_game_generator(game_id, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
