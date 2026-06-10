from typing import TypedDict


class OSCAState(TypedDict, total=False):
    user_id: int
    github_token: str
    profile: dict
    skill_profile: dict
    candidate_issues: list[dict]
    ranked_matches: list[dict]
    learning_gaps: list[str]
    learning_resources: list[dict]
    codebase_insights: dict
    errors: list[str]
