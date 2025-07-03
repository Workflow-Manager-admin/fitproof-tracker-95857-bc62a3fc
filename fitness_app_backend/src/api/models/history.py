"""
Models for workout session history, including database ORM and Pydantic schemas.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .user import Base

# SQLAlchemy ORM model
class WorkoutSession(Base):
    """Database model for a workout session proof uploaded by a user."""
    __tablename__ = "workout_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_name = Column(String, nullable=True)  # Optional exercise type/name
    media_url = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # "image" or "video"
    timer_seconds = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="workout_sessions")


# PUBLIC_INTERFACE
class WorkoutSessionRead(BaseModel):
    """Response schema for a single workout session/proof."""
    id: int
    exercise_name: Optional[str] = Field(None, description="Name of the exercise (optional)")
    media_url: str = Field(..., description="Remote URL of proof media")
    media_type: str = Field(..., description="Type of media: 'image' or 'video'")
    timer_seconds: Optional[int] = Field(None, description="Workout duration in seconds")
    timestamp: datetime = Field(..., description="Timestamp of upload/session")

    class Config:
        orm_mode = True


# PUBLIC_INTERFACE
class WorkoutHistoryResponse(BaseModel):
    """Full response schema for the history endpoint."""
    user_id: int
    sessions: list[WorkoutSessionRead] = Field(..., description="All workout sessions uploaded by the user")
