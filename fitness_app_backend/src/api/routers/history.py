"""
Workout history retrieval endpoints, including GET /workout/history.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.api.models.user import User as UserModel
from src.api.models.history import WorkoutSession, WorkoutHistoryResponse, WorkoutSessionRead

router = APIRouter(
    prefix="/workout",
    tags=["Workout History"],
    responses={404: {"description": "Not found"}},
)

# PUBLIC_INTERFACE
@router.get(
    "/history",
    response_model=WorkoutHistoryResponse,
    summary="Get user's workout session history",
    description="Returns all workout sessions with media, timer, and timestamps for the authenticated user."
)
def get_workout_history(
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """
    Fetch workout session history for the requesting user, including proof media.
    """
    sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.timestamp.desc())
        .all()
    )

    session_items = [
        WorkoutSessionRead.from_orm(s) for s in sessions
    ]

    return WorkoutHistoryResponse(
        user_id=user.id,
        sessions=session_items,
    )
