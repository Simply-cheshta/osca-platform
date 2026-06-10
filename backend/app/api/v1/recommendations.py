from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.security import decrypt_token
from app.models.user import User
from app.services.github_client import GitHubClient, MOCK_ISSUES
from app.services.matching_service import extract_skill_keywords

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _get_matching_service():
    from app.dependencies import matching_service
    return matching_service


def _get_profile_service():
    from app.dependencies import profile_service
    return profile_service


@router.get("/issues")
async def get_recommendations(
    profile_bio: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    limit: int = Query(30, ge=5, le=50),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    matching = _get_matching_service()
    profile_svc = _get_profile_service()

    manual_bio = (profile_bio or "").strip()
    profile_text = manual_bio
    skill_tags: list[str] = []

    if current_user:
        cached = profile_svc.get_profile_dict(current_user, db)
        if cached and not manual_bio:
            profile_text = cached.get("profile_text", profile_text)
            skill_tags = list(cached.get("skill_tags", []))
        elif cached and manual_bio:
            # Merge manual bio with GitHub profile when user types skills
            profile_text = f"{manual_bio}. {cached.get('profile_text', '')}"
            skill_tags = list(cached.get("skill_tags", []))
        elif not profile_text:
            profile_text = current_user.bio or f"Developer {current_user.github_username}"

    if manual_bio:
        skill_tags = list(dict.fromkeys(extract_skill_keywords(manual_bio) + skill_tags))

    if not profile_text:
        profile_text = "Open source software developer interested in contributing to GitHub projects."

    token = None
    if current_user and current_user.access_token_encrypted:
        token = decrypt_token(current_user.access_token_encrypted)

    github = GitHubClient(token)
    search_label = language or (skill_tags[0] if skill_tags else None)
    issues = await github.search_issues(language=search_label, per_page=limit)
    if not issues:
        issues = MOCK_ISSUES

    ranked = matching.rank_issues(
        profile_text=profile_text,
        skill_tags=skill_tags,
        issues=issues,
        explain_top_n=5,
    )

    return {"recommendations": ranked, "profile_used": profile_text[:200]}
