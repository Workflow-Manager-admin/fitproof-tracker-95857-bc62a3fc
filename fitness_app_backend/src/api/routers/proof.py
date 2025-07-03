"""
API router for handling workout proof (image/video) uploads
with Cloudinary integration and optional timer metadata.
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Annotated, Literal, Optional
import tempfile
import shutil

from src.api.dependencies import get_db, get_current_user
from src.api.models.user import User as UserModel
from src.api.models.proof import ProofUploadResponse
from src.api.cloudinary_service.upload import upload_proof_media

# Import the workout history model
from src.api.models.history import WorkoutSession

router = APIRouter(
    prefix="/proof",
    tags=["Workout Proof"],
    responses={404: {"description": "Not found"}},
)

# PUBLIC_INTERFACE
@router.post(
    "/upload",
    response_model=ProofUploadResponse,
    summary="Upload workout image/video proof",
    description=(
        "Upload workout proof media (image or video) with optional workout timer metadata. "
        "Stores the file in Cloudinary and associates with authenticated user."
    ),
)
async def upload_proof(
    media_file: Annotated[UploadFile, File(..., description="Media file (image or video) to upload")],
    media_type: Annotated[Literal["image", "video"], Form(..., description="Type of media file (image or video)")],
    workout_timer_seconds: Annotated[Optional[int], Form(None, description="Duration (seconds) of the workout session")] = None,
    user: UserModel = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Handle upload of workout proof media to Cloudinary, associating
    it with the authenticated user and attaching timer metadata, and persist in history.
    """
    # Validate media type
    allowed_types = ("image", "video")
    if media_type not in allowed_types:
        raise HTTPException(status_code=400, detail="media_type must be 'image' or 'video'.")

    # Save file temporarily
    try:
        suffix = ".jpg" if media_type == "image" else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(media_file.file, tmp)
            tmp.flush()
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Upload to Cloudinary
    try:
        result = upload_proof_media(
            file_path=tmp_path,
            user_id=user.id,
            media_type=media_type,
            workout_timer_seconds=workout_timer_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary upload failed: {str(e)}"
        )
    finally:
        try:
            import os
            os.remove(tmp_path)
        except Exception:
            pass

    # Save to workout history in DB
    session_obj = WorkoutSession(
        user_id=user.id,
        media_url=result["url"],
        media_type=media_type,
        timer_seconds=workout_timer_seconds,
    )
    db.add(session_obj)
    db.commit()

    return ProofUploadResponse(
        url=result["url"],
        public_id=result["public_id"],
        media_type=result["media_type"],
        workout_timer_seconds=result.get("workout_timer_seconds"),
        detail="Upload succeeded.",
    )
