from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decrypt_token
from app.models.user import User
from app.schemas.profile import ProfileResponse
from app.services.github_client import GitHubClient

router = APIRouter(prefix="/profile", tags=["User Profile"])


def _get_profile_service():
    from app.dependencies import profile_service
    return profile_service


@router.get("", response_model=ProfileResponse)
async def get_cached_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return cached profile from DB without hitting GitHub."""
    service = _get_profile_service()
    cached = service.get_profile_dict(current_user, db)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile yet. Click Sync Profile to analyze your GitHub account.",
        )
    return cached


@router.get("/analyze", response_model=ProfileResponse)
async def analyze_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _get_profile_service()
    try:
        result = await service.analyze_and_persist(current_user, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/contributions")
async def get_contributions(current_user: User = Depends(get_current_user)):
    token = decrypt_token(current_user.access_token_encrypted)
    if not token:
        raise HTTPException(status_code=401, detail="No GitHub token")
    github = GitHubClient(token)
    prs = await github.get_user_pull_requests()
    return {"contributions": prs}
