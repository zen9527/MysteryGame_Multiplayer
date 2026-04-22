from fastapi import FastAPI
from server.websocket_hub import router as ws_router
from server.api_routes import router as api_router
from server.middleware import CORSMiddleware

app = FastAPI(title="剧本杀服务器", version="1.0.0")

app.add_middleware(CORSMiddleware)
app.include_router(ws_router)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    from server.config import config
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
