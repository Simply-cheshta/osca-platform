from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


def _get_services():
    from app.dependencies import llm_service, qdrant_service, vector_service
    return vector_service, llm_service, qdrant_service


@router.get("/health")
async def health_check():
    vector_service, llm_service, qdrant_service = _get_services()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "embedding_model": settings.EMBEDDING_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "qdrant_available": qdrant_service.is_available,
        "github_oauth_configured": bool(settings.GITHUB_CLIENT_ID),
    }
