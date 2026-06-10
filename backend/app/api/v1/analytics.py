from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.agent_run import AgentRun
from app.models.issue import BookmarkedIssue
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_profile_service():
    from app.dependencies import profile_service
    return profile_service


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile_svc = _get_profile_service()
    profile = profile_svc.get_profile_dict(current_user, db)

    bookmark_count = (
        db.query(BookmarkedIssue)
        .filter(BookmarkedIssue.user_id == current_user.id)
        .count()
    )
    agent_runs = (
        db.query(AgentRun)
        .filter(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "user": {
            "username": current_user.github_username,
            "avatar_url": current_user.avatar_url,
        },
        "profile": profile,
        "stats": {
            "bookmarks": bookmark_count,
            "agent_runs": len(agent_runs),
            "experience_level": profile.get("experience_level") if profile else "unknown",
        },
        "recent_runs": [
            {
                "id": r.id,
                "status": r.status,
                "workflow_type": r.workflow_type,
                "duration_ms": r.duration_ms,
            }
            for r in agent_runs
        ],
    }
