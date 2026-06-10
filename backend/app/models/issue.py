from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BookmarkedIssue(Base):
    __tablename__ = "bookmarked_issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    github_issue_id = Column(Integer, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    labels = Column(String(500), nullable=True)
    html_url = Column(String(500), nullable=False)
    match_score = Column(Integer, nullable=True)
    difficulty = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookmarks")
