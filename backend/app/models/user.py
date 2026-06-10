from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    github_username = Column(String(255), unique=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    access_token_encrypted = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bookmarks = relationship("BookmarkedIssue", back_populates="user")


class SkillProfile(Base):
    __tablename__ = "skill_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    profile_text = Column(Text, nullable=False, default="")
    top_languages = Column(Text, nullable=True)  # comma-separated
    skill_tags = Column(Text, nullable=True)
    experience_level = Column(String(20), default="intermediate")
    frontend_score = Column(Integer, default=0)
    backend_score = Column(Integer, default=0)
    dsa_score = Column(Integer, default=0)
    open_source_readiness = Column(Integer, default=0)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

