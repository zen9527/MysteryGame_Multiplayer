from fastapi import APIRouter, HTTPException
from server.di import container

router = APIRouter()


@router.get("/health")
async def health_check():
    """Comprehensive health check including LLM and game manager."""
    status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check LLM provider
    try:
        registry = container.resolve("llm_registry")
        active_provider = registry.get_active()
        if active_provider:
            status["checks"]["llm"] = {
                "status": "healthy",
                "provider": active_provider.name
            }
        else:
            status["checks"]["llm"] = {
                "status": "unhealthy",
                "message": "No active LLM provider"
            }
            status["status"] = "unhealthy"
    except Exception as e:
        status["checks"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    # Check game manager
    try:
        manager = container.resolve("game_manager")
        status["checks"]["game_manager"] = {
            "status": "healthy",
            "active_games": len(manager.games)
        }
    except Exception as e:
        status["checks"]["game_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    # Check database
    try:
        repo = container.resolve("script_repository")
        cursor = repo.conn.execute("SELECT 1")
        result = cursor.fetchone()
        if result and result[0] == 1:
            status["checks"]["database"] = {
                "status": "healthy",
                "type": "sqlite"
            }
        else:
            status["checks"]["database"] = {
                "status": "unhealthy",
                "message": "Database query failed"
            }
            status["status"] = "unhealthy"
    except Exception as e:
        status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    return status


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    health = await health_check()
    if health["status"] == "healthy":
        return health
    else:
        raise HTTPException(status_code=503, detail="Not ready")
