from typing import Optional

from pydantic import BaseModel


class BookmarkCreate(BaseModel):
    github_issue_id: int | str
    title: str
    description: Optional[str] = None
    labels: Optional[str] = None
    html_url: str
    match_score: Optional[float] = None
    difficulty: Optional[str] = None


class BookmarkResponse(BaseModel):
    id: int
    github_issue_id: int
    title: str
    description: Optional[str] = None
    labels: list[str] = []
    html_url: str
    match_score: Optional[float] = None
    difficulty: Optional[str] = None

    class Config:
        from_attributes = True
