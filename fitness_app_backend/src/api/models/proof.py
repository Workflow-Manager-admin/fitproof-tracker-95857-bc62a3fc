"""Pydantic models for proof upload and metadata."""

from pydantic import BaseModel, Field
from typing import Literal, Optional

# PUBLIC_INTERFACE
class ProofUploadResponse(BaseModel):
    """Response model for a successful proof upload."""
    url: str = Field(..., description="URL of the uploaded media file on Cloudinary")
    public_id: str = Field(..., description="Cloudinary public_id for reference")
    media_type: Literal["image", "video"] = Field(..., description="Media file type")
    workout_timer_seconds: Optional[int] = Field(None, description="Duration (seconds) of the workout session")
    detail: str = Field(..., description="Upload status message")

# PUBLIC_INTERFACE
class TimerMetadata(BaseModel):
    """Metadata about the workout timer that can be attached to a proof."""
    workout_timer_seconds: int = Field(..., description="Duration (seconds) of the workout session")
