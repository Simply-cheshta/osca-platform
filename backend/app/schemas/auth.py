from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    github_username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True
