"""
Cloudinary upload logic for proof media (image/video) files.
"""

import os
import cloudinary
import cloudinary.uploader
from typing import Literal

# Initialize Cloudinary only once, using environment variables for config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# PUBLIC_INTERFACE
def upload_proof_media(
    file_path: str,
    user_id: int,
    media_type: Literal["image", "video"] = "image",
    workout_timer_seconds: int | None = None,
    **extra
) -> dict:
    """
    Uploads image or video proof using Cloudinary.

    Args:
        file_path: The path to the local file to upload.
        user_id: User ID associated with the proof.
        media_type: "image" or "video".
        workout_timer_seconds: Optional exercise session duration.
        extra: Any additional Cloudinary upload options.

    Returns:
        dict with keys: url, public_id, media_type, workout_timer_seconds, and Cloudinary upload result.
    """
    resource_type = "image" if media_type == "image" else "video"
    folder = f"fitproof-tracker/user_{user_id}/"
    public_id = os.path.splitext(os.path.basename(file_path))[0]

    response = cloudinary.uploader.upload(
        file_path,
        resource_type=resource_type,
        folder=folder,
        public_id=public_id,
        use_filename=True,
        unique_filename=False,
        overwrite=True,
        tags=["workout_proof"],
        **extra,
    )

    return {
        "url": response.get("secure_url"),
        "public_id": response.get("public_id"),
        "media_type": media_type,
        "workout_timer_seconds": workout_timer_seconds,
        "cloudinary_result": response,
    }
