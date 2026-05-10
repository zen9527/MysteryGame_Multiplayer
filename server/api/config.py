from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from starlette.concurrency import run_in_threadpool
from server.di import container
from server.utils.endpoint import normalize_endpoint
from server.utils.validation import mask_api_key

router = APIRouter()


def _get_host_dm():
    return container.resolve("host_dm")


def _get_manager():
    return container.resolve("game_manager")


class LLMConfigRequest(BaseModel):
    endpoint: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


@router.get("/llm-config")
async def get_llm_config():
    config = _get_host_dm().llm.get_config()
    config["api_key_masked"] = mask_api_key(_get_host_dm().llm.api_key)
    if "api_key" in config:
        del config["api_key"]
    return config


@router.post("/llm-config")
async def update_llm_config(req: LLMConfigRequest):
    if req.endpoint is not None:
        normalized = normalize_endpoint(req.endpoint)
        if not normalized:
            raise HTTPException(status_code=400, detail="无效的 LLM 端点 URL")
    _get_host_dm().llm.set_runtime_config(
        endpoint=req.endpoint,
        model=req.model,
        api_key=req.api_key,
    )
    config = _get_host_dm().llm.get_config()
    config["api_key_masked"] = mask_api_key(_get_host_dm().llm.api_key)
    if "api_key" in config:
        del config["api_key"]
    return {"status": "updated", **config}


@router.post("/test-llm")
async def test_llm(req: Optional[LLMConfigRequest] = None):
    orig_endpoint = _get_host_dm().llm.endpoint
    orig_model = _get_host_dm().llm.model
    orig_api_key = _get_host_dm().llm.api_key

    if req and (req.endpoint or req.model or req.api_key is not None):
        endpoint_to_use = normalize_endpoint(req.endpoint) if req.endpoint else orig_endpoint
        model_to_use = req.model if req.model else orig_model
        api_key_to_use = req.api_key if req.api_key is not None else orig_api_key
        _get_host_dm().llm.set_runtime_config(
            endpoint=endpoint_to_use,
            model=model_to_use,
            api_key=api_key_to_use,
        )

    try:
        import time
        start = time.time()
        result = await run_in_threadpool(_get_host_dm().llm.test_connection)
        elapsed = time.time() - start
        return {
            "status": "connected",
            "response_time_ms": round(elapsed * 1000),
            "model": _get_host_dm().llm.model,
            "endpoint": _get_host_dm().llm.endpoint,
            "sample_response": result[:200],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        _get_host_dm().llm.set_runtime_config(
            endpoint=orig_endpoint,
            model=orig_model,
            api_key=orig_api_key,
        )


@router.get("/llm-models")
async def list_llm_models():
    try:
        models = await run_in_threadpool(_get_host_dm().llm.list_models)
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@router.get("/health")
async def health_check():
    return {"status": "ok", "games_count": len(_get_manager().games)}
