from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db, get_current_user
from src.api.models.user import (
    User as UserModel,
    UserProfileInput,
    UserProfileOutput,
    ExerciseRecommendationResponse,
)

router = APIRouter(
    prefix="",
    tags=["User Profile & Recommendations"],
    responses={404: {"description": "Not found"}},
)

# PUBLIC_INTERFACE
@router.post(
    "/user/profile",
    response_model=UserProfileOutput,
    summary="Submit or update user's physical profile",
    description="Submit or update the height and weight of the current user.",
)
def update_user_profile(
    profile: UserProfileInput,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """Update the current user's height and weight."""
    db_user = db.query(UserModel).filter(UserModel.id == user.id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    db_user.height_cm = profile.height_cm
    db_user.weight_kg = profile.weight_kg
    db.commit()
    db.refresh(db_user)
    return UserProfileOutput(height_cm=db_user.height_cm, weight_kg=db_user.weight_kg)


# PUBLIC_INTERFACE
@router.post(
    "/exercise/recommend",
    response_model=ExerciseRecommendationResponse,
    summary="Recommend exercises for user",
    description="Recommends exercises tailored to the authenticated user's height and weight.",
)
def recommend_exercise(
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    """Recommend exercises for the current user based on their physical profile."""
    if user.height_cm is None or user.weight_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile incomplete: height and weight required.",
        )

    # Simple recommendation logic (placeholder):
    # • Recommend more cardio if BMI is high, focus on strength if low, etc.
    # For real use: replace logic with ML model or more advanced rules.

    # Calculate BMI = kg / (m^2)
    height_m = user.height_cm / 100.0
    bmi = user.weight_kg / (height_m * height_m)

    if bmi < 18.5:
        exercises = [
            "Full-body strength training",
            "Bodyweight squats",
            "Push-ups",
            "Lunges",
            "Plank holds",
            "Healthy eating guidance",
        ]
    elif bmi < 25:
        exercises = [
            "Mixed cardio and strength",
            "Running or brisk walking",
            "Plank and core strengthening",
            "Squats and lunges",
            "Jump rope",
        ]
    elif bmi < 30:
        exercises = [
            "Low-impact cardio",
            "Cycling",
            "Swimming",
            "Leg raises",
            "Step-ups",
            "Fitness walking",
        ]
    else:
        exercises = [
            "Gentle cardio (walking, swimming)",
            "Chair exercises",
            "Stretching and mobility drills",
            "Consult a health professional before starting",
        ]

    return ExerciseRecommendationResponse(recommended_exercises=exercises)
