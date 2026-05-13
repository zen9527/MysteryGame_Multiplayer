from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from server.di import container

router = APIRouter()


def _get_registry():
    return container.resolve("llm_registry")


def _get_manager():
    return container.resolve("game_manager")


class ProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., pattern=r"^(openai|anthropic|gemini)$")
    endpoint: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    api_key: str = ""


class ActiveProviderRequest(BaseModel):
    name: str = Field(..., min_length=1)


@router.get("/llm/providers")
async def list_providers():
    return {"providers": _get_registry().list_providers()}


@router.post("/llm/providers")
async def add_provider(req: ProviderCreateRequest):
    registry = _get_registry()
    try:
        provider = registry.create_provider(req.type, req.name,
                                            endpoint=req.endpoint,
                                            model=req.model,
                                            api_key=req.api_key)
        registry.register(req.name, provider)
        return {"status": "added", "name": req.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/llm/providers/{name}")
async def remove_provider(name: str):
    registry = _get_registry()
    providers = {p["name"] for p in registry.list_providers()}
    if name not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    registry.remove(name)
    return {"status": "removed"}


@router.post("/llm/providers/active")
async def set_active_provider(req: ActiveProviderRequest):
    registry = _get_registry()
    try:
        registry.set_active(req.name)
        return {"status": "active", "name": req.name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/llm/providers/{name}/test")
async def test_provider(name: str):
    registry = _get_registry()
    try:
        provider = registry.get(name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")

    import time
    try:
        start = time.time()
        result = await run_in_threadpool(provider.test_connection)
        elapsed = time.time() - start
        return {
            "status": "connected",
            "response_time_ms": round(elapsed * 1000),
            "model": provider.model,
            "sample_response": result[:200],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/llm/providers/{name}/models")
async def list_provider_models(name: str):
    registry = _get_registry()
    try:
        provider = registry.get(name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")
    try:
        models = await run_in_threadpool(provider.list_models)
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


# Proxy endpoint for frontend to fetch models (avoids CORS)
@router.get("/llm/models")
async def proxy_fetch_models():
    """Proxy endpoint for frontend to fetch LLM models.
    Frontend calls this instead of directly calling the LLM provider API.
    """
    registry = _get_registry()
    try:
        provider = registry.get_active()
    except ValueError:
        raise HTTPException(status_code=404, detail="No active provider")
    try:
        models = await run_in_threadpool(provider.list_models)
        return {"data": [{"id": m, "object": "model"} for m in models]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Backward-compatible endpoints
@router.get("/llm-config")
async def get_llm_config():
    return _get_registry().get_active().get_config()


@router.get("/health")
async def health_check():
    return {"status": "ok"}
