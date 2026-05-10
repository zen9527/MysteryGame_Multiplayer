from fastapi import APIRouter
from server.api.rooms import router as rooms_router
from server.api.script import router as script_router
from server.api.game import router as game_router
from server.api.dm import router as dm_router
from server.api.voting import router as voting_router
from server.api.chat import router as chat_router
from server.api.config import router as config_router

router = APIRouter()

# Include all domain routers
router.include_router(rooms_router)
router.include_router(script_router)
router.include_router(game_router)
router.include_router(dm_router)
router.include_router(voting_router)
router.include_router(chat_router)
router.include_router(config_router)
