from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    workflow_type = Column(String(50), default="full_match")
    status = Column(String(20), default="running")
    state_snapshot = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
