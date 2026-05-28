from fastapi import APIRouter

from src.api.v1.advisor import router as advisor_router
from src.api.v1.auth import router as auth_router
from src.api.v1.chat import router as chat_router
from src.api.v1.compare import router as compare_router
from src.api.v1.health import router as health_router
from src.api.v1.modules import router as modules_router
from src.api.v1.sessions import router as sessions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(advisor_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(modules_router)
api_v1_router.include_router(compare_router)
api_v1_router.include_router(sessions_router)
