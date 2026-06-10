from typing import Optional

from pydantic import BaseModel


class SkillMetrics(BaseModel):
    frontend_score: float
    backend_score: float
    dsa_score: float
    open_source_readiness: str


class ProfileResponse(BaseModel):
    github_username: str
    avatar_url: Optional[str] = None
    public_repos: Optional[int] = None
    bio: Optional[str] = None
    top_languages: list[str] = []
    skill_tags: list[str] = []
    profile_text: str = ""
    experience_level: str = "intermediate"
    metrics: SkillMetrics
