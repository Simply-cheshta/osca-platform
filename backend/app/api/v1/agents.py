from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decrypt_token
from app.models.user import User

router = APIRouter(prefix="/agents", tags=["Agents"])


class PRReviewRequest(BaseModel):
    issue_title: str
    diff_text: str


def _get_orchestrator():
    from app.dependencies import agent_orchestrator, llm_service
    return agent_orchestrator, llm_service


@router.post("/match")
async def run_match_workflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = decrypt_token(current_user.access_token_encrypted)
    if not token:
        raise HTTPException(status_code=400, detail="No GitHub token. Re-authenticate.")

    orchestrator, _ = _get_orchestrator()
    result = await orchestrator.run_full_match(current_user.id, token, db)
    return result


@router.get("/runs/{run_id}")
async def get_agent_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orchestrator, _ = _get_orchestrator()
    run = orchestrator.get_run(run_id, db)
    if not run or (run.user_id and run.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "workflow_type": run.workflow_type,
        "status": run.status,
        "duration_ms": run.duration_ms,
        "state_snapshot": run.state_snapshot,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.post("/pr-review")
async def pr_review(
    body: PRReviewRequest,
    current_user: User = Depends(get_current_user),
):
    _, llm_service = _get_orchestrator()
    feedback = llm_service.review_pr(body.issue_title, body.diff_text)
    return {"feedback": feedback}
