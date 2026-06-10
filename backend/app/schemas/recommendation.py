from typing import Optional

from pydantic import BaseModel


class IssueRecommendation(BaseModel):
    id: int
    title: str
    description: str
    labels: list[str] = []
    html_url: str
    match_score: float
    difficulty: str = "medium"
    difficulty_confidence: float = 0.5
    explanation: Optional[str] = None
    repo_name: Optional[str] = None
