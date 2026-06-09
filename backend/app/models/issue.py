from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base

class BookmarkedIssue(Base):
    """
    SQLAlchemy database table model for saving and tracking open-source
    issues a contributor intends to work on.
    """
    __tablename__ = "bookmarked_issues"

    id = Column(Integer, primary_key=True, index=True)
    github_issue_id = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    labels = Column(String(255), nullable=True)  
    html_url = Column(String(500), nullable=False)