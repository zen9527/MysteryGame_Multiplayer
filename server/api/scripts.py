from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from server.di import container
from server.config import config
import json

router = APIRouter()


def _get_service():
    return container.resolve("script_service")


class ScriptGenerationRequest(BaseModel):
    genre: str
    difficulty: str = "中等"
    estimated_time: int = 90
    player_count: int = 4


def require_script_admin(admin_key: str = Query(..., alias="admin_key")):
    """Admin key check for script management endpoints. Key set via SCRIPT_ADMIN_KEY env var."""
    if not config.SCRIPT_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Script admin key not configured")
    if admin_key != config.SCRIPT_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


class ScriptUploadRequest(BaseModel):
    title: str
    genre: Optional[str] = None
    difficulty: Optional[str] = None
    player_count: Optional[int] = None
    estimated_time: Optional[int] = None
    background_story: Optional[str] = None
    true_killer: str
    murder_method: str
    cover_up: str
    roles: List[dict]
    clues: List[dict]
    plot_outline: dict
    private_events: Optional[List[dict]] = []


@router.get("/scripts")
async def list_scripts(
    genre: Optional[str] = None,
    difficulty: Optional[str] = None,
    min_players: Optional[int] = None
):
    service = _get_service()
    scripts = service.list_scripts(genre, difficulty, min_players)
    return {"scripts": scripts}


@router.get("/scripts/export")
async def export_scripts(admin: bool = Depends(require_script_admin)):
    scripts = _get_service().export_all()
    return {"scripts": scripts}


@router.post("/scripts/import")
async def import_scripts(req: dict, admin: bool = Depends(require_script_admin)):
    scripts = req.get("scripts", [])
    count = _get_service().import_scripts(scripts)
    return {"imported": count}


@router.post("/scripts")
async def upload_script(req: ScriptUploadRequest, admin: bool = Depends(require_script_admin)):
    script_data = req.model_dump()
    script_id = _get_service().upload(script_data)
    return {"script_id": script_id}


@router.get("/scripts/{script_id}")
async def get_script_detail(script_id: str):
    service = _get_service()
    detail = service.get_detail(script_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Script not found")
    return detail


@router.delete("/scripts/{script_id}")
async def delete_script(script_id: str, admin: bool = Depends(require_script_admin)):
    if not _get_service().delete(script_id):
        raise HTTPException(status_code=404, detail="Script not found")
    return {"message": "Script deleted"}


def _generate_script_standalone_generator(req: ScriptGenerationRequest):
    """Generator for standalone script generation (no room context)."""
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

        # Return the full script data
        script_data = script.model_dump()
        yield f"data: {{\"type\": \"done\", \"data\": {json.dumps(script_data, ensure_ascii=False)}}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/scripts/generate")
async def generate_script_standalone(req: ScriptGenerationRequest):
    """Standalone script generation endpoint (no room required)."""
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        _generate_script_standalone_generator(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
