from pydantic import BaseModel
from typing import Optional

class BookmarkCreate(BaseModel):
    github_issue_id: int
    title: str
    description: Optional[str] = None
    labels: Optional[str] = None
    html_url: str