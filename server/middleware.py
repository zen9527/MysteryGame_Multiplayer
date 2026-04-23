from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from server.game_manager import manager


class CORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Player-ID, X-Admin-Key"
        return response


def require_admin(player_id: str, game_id: str):
    """校验管理员权限，非管理员抛出 403"""
    if not manager.is_admin(game_id, player_id):
        raise HTTPException(status_code=403, detail="仅管理员可操作")
