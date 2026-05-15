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


@router.put("/scripts/{script_id}")
async def update_script(script_id: str, req: dict, admin: bool = Depends(require_script_admin)):
    """Update a script and create a new version"""
    service = _get_service()
    
    # Check if script exists
    existing = service.get_detail(script_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Update the script
    updated = service.update(script_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Create a version snapshot
    version_repo = container.resolve("script_version_repository")
    version_id = version_repo.create_version(
        script_id=script_id,
        data=req,
        notes="Manual update"
    )
    
    return {
        "id": script_id,
        "updated_at": updated.get("created_at"),
        "version_id": version_id
    }


# Version management endpoints
@router.get("/scripts/{script_id}/versions")
async def get_script_versions(script_id: str):
    """Get all versions for a script"""
    version_repo = container.resolve("script_version_repository")
    versions = version_repo.get_script_versions(script_id)
    
    # Return metadata only (not full data)
    return {
        "versions": [
            {
                "version_id": v["id"],
                "version_number": v["version_number"],
                "created_at": v["created_at"],
                "created_by": v.get("created_by"),
                "notes": v.get("notes")
            }
            for v in versions
        ]
    }


@router.get("/scripts/{script_id}/versions/{version_id}")
async def get_script_version(script_id: str, version_id: str):
    """Get a specific version's full data"""
    version_repo = container.resolve("script_version_repository")
    version = version_repo.get_version(version_id)
    
    if not version or version["script_id"] != script_id:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {
        "version_id": version["id"],
        "version_number": version["version_number"],
        "created_at": version["created_at"],
        "created_by": version.get("created_by"),
        "notes": version.get("notes"),
        "data": version["data"]
    }


@router.post("/scripts/{script_id}/versions/{version_id}/restore")
async def restore_script_version(script_id: str, version_id: str, admin: bool = Depends(require_script_admin)):
    """Restore a script to a specific version"""
    version_repo = container.resolve("script_version_repository")
    
    restored = version_repo.restore_version(version_id)
    if not restored or restored["script_id"] != script_id:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {
        "message": "Version restored",
        "new_version_id": restored["id"],
        "restored_from": version_id
    }


@router.get("/scripts/versions/compare")
async def compare_versions(
    version_id_1: str = Query(..., description="First version ID"),
    version_id_2: str = Query(..., description="Second version ID")
):
    """Compare two versions"""
    version_repo = container.resolve("script_version_repository")
    result = version_repo.compare_versions(version_id_1, version_id_2)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


def _generate_script_standalone_generator(req: ScriptGenerationRequest):
    """Generator for standalone script generation (no room context)."""
    from server.script_engine.models import ScriptV2
    script_gen = container.resolve("script_generator")

    try:
        # Step 1: Building prompt
        yield f"data: {{\"type\": \"status\", \"step\": 1, \"total_steps\": 5, \"message\": \"正在构建提示词...\"}}\n\n"
        
        yield f"data: {{\"type\": \"start\"}}\n\n"

        # Step 2: Calling LLM (send status BEFORE the call so frontend doesn't hang)
        yield f"data: {{\"type\": \"status\", \"step\": 2, \"total_steps\": 5, \"message\": \"正在调用 AI 生成剧本...\"}}\n\n"
        
        full_text = ""
        chunk_count = 0
        for chunk in script_gen.generate_stream(req.genre, req.difficulty, req.player_count, req.estimated_time):
            full_text += chunk
            chunk_count += 1
            
            # Send progress updates every 10 chunks for smoother progress
            if chunk_count % 10 == 0:
                # Map chunk progress to 40%-85% range (step 2 ends at 36%, step 4 starts at ~80%)
                progress = min(85, 40 + int((chunk_count / 400) * 45))
                msg = f"正在生成剧本内容... ({progress}%)"
                status_event = {"type": "status", "step": 3, "total_steps": 5, "message": msg}
                yield f"data: {json.dumps(status_event, ensure_ascii=False)}\n\n"
            
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        # Step 4: Parsing and normalizing
        yield f"data: {{\"type\": \"status\", \"step\": 4, \"total_steps\": 5, \"message\": \"正在解析和验证剧本...\"}}\n\n"
        
        script_dict = script_gen.normalize_script_json(full_text)
        script = ScriptV2(**script_dict)

        # Step 5: Complete
        yield f"data: {{\"type\": \"status\", \"step\": 5, \"total_steps\": 5, \"message\": \"剧本生成完成！\"}}\n\n"
        
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
