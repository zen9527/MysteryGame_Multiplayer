from contextlib import asynccontextmanager
from fastapi import FastAPI
from server.websocket_hub import router as ws_router
from server.api import router as api_router
from server.middleware import CORSMiddleware, ValidateRequestMiddleware
from server.di import register_services, container
import asyncio

# Register all services at startup
register_services(container)

_cleanup_task = None


async def _periodic_cleanup():
    """Background task: periodically cleanup ended/abandoned games."""
    manager = container.resolve("game_manager")
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        try:
            manager.cleanup_all()
            manager.cleanup_abandoned()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[Cleanup] Error: {e}")


@asynccontextmanager
async def lifespan(app):
    global _cleanup_task
    _cleanup_task = asyncio.create_task(_periodic_cleanup())
    yield
    if _cleanup_task:
        _cleanup_task.cancel()


app = FastAPI(title="剧本杀服务器", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware)
app.add_middleware(ValidateRequestMiddleware)
app.include_router(ws_router)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    from server.config import config
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
