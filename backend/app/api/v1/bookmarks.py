from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.models.issue import BookmarkedIssue
from app.models.user import User
from app.schemas.bookmark import BookmarkCreate

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


def _format_bookmark(item: BookmarkedIssue) -> dict:
    labels = []
    if item.labels:
        labels = [l.strip() for l in item.labels.split(",") if l.strip()]
    return {
        "id": item.id,
        "github_issue_id": item.github_issue_id,
        "title": item.title,
        "description": item.description,
        "labels": labels,
        "html_url": item.html_url,
        "match_score": item.match_score,
        "difficulty": item.difficulty,
    }


@router.post("", status_code=201)
async def create_bookmark(
    bookmark: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    issue_id = int(bookmark.github_issue_id)
    query = db.query(BookmarkedIssue).filter(
        BookmarkedIssue.github_issue_id == issue_id
    )
    if current_user:
        query = query.filter(BookmarkedIssue.user_id == current_user.id)
    if query.first():
        raise HTTPException(status_code=400, detail="Already bookmarked.")

    db_bookmark = BookmarkedIssue(
        user_id=current_user.id if current_user else None,
        github_issue_id=issue_id,
        title=bookmark.title,
        description=bookmark.description,
        labels=bookmark.labels,
        html_url=bookmark.html_url,
        match_score=int(bookmark.match_score) if bookmark.match_score else None,
        difficulty=bookmark.difficulty,
    )
    try:
        db.add(db_bookmark)
        db.commit()
        db.refresh(db_bookmark)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not save bookmark: {e}") from e
    return {"message": "Bookmarked", "bookmark": _format_bookmark(db_bookmark)}


@router.get("")
async def get_bookmarks(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    query = db.query(BookmarkedIssue)
    if current_user:
        query = query.filter(BookmarkedIssue.user_id == current_user.id)
    bookmarks = query.order_by(BookmarkedIssue.id.desc()).all()
    return {"bookmarked_issues": [_format_bookmark(b) for b in bookmarks]}


@router.delete("/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    query = db.query(BookmarkedIssue).filter(BookmarkedIssue.id == bookmark_id)
    if current_user:
        query = query.filter(BookmarkedIssue.user_id == current_user.id)
    item = query.first()
    if not item:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
