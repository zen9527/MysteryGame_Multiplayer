from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from server.game_manager import manager
import re


class ValidateRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Validate and sanitize incoming requests."""
        
        # Skip validation for health checks and static files
        if request.url.path.startswith(('/health', '/static')):
            return await call_next(request)
        
        # Validate Content-Type for POST/PUT requests to API endpoints
        if request.method in ['POST', 'PUT'] and request.url.path.startswith('/api/'):
            content_type = request.headers.get('content-type', '')
            
            # Check if request has a body
            try:
                body = await request.json()
            except:
                body = None
            
            # If no body and endpoint doesn't require JSON, allow it through
            if body is None and 'application/json' not in content_type:
                # Allow endpoints that typically don't need a body
                allowed_endpoints = ['/start', '/advance-act', '/force-trial', '/end-game']
                if any(endpoint in request.url.path for endpoint in allowed_endpoints):
                    return await call_next(request)
                # Allow upload/import endpoints
                if any(endpoint in request.url.path for endpoint in ['/upload', '/import']):
                    return await call_next(request)
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type must be application/json"}
                )
        
        response = await call_next(request)
        return response


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
