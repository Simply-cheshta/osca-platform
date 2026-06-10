from fastapi import APIRouter

from app.api.v1 import agents, analytics, auth, bookmarks, health, profile, recommendations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(recommendations.router)
api_router.include_router(bookmarks.router)
api_router.include_router(agents.router)
api_router.include_router(analytics.router)
api_router.include_router(health.router)
