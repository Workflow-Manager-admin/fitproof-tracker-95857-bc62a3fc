"""User SQLAlchemy model and related Pydantic schemas for the Fitness App."""

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr, Field

Base = declarative_base()

class User(Base):
    """Database user model."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    height_cm = Column(Float, nullable=True)  # Height in centimeters
    weight_kg = Column(Float, nullable=True)  # Weight in kilograms

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Pydantic schema for creating a new user."""
    email: EmailStr = Field(..., description="Email address of user")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Pydantic schema for logging in a user."""
    email: EmailStr = Field(..., description="Email address of user")
    password: str = Field(..., description="User password")

# PUBLIC_INTERFACE
class UserRead(BaseModel):
    """Response schema for returning user info (excluding password)."""
    id: int
    email: EmailStr
    height_cm: float | None = None
    weight_kg: float | None = None

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class UserProfileInput(BaseModel):
    """Input schema for updating user's physical profile (height, weight)."""
    height_cm: float = Field(..., gt=0, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")

# PUBLIC_INTERFACE
class UserProfileOutput(BaseModel):
    """Output schema for user's physical profile."""
    height_cm: float
    weight_kg: float

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class ExerciseRecommendationRequest(BaseModel):
    """Schema for requesting exercise recommendations."""
    # The schema is empty because we'll get user from JWT, but could expand
    pass

# PUBLIC_INTERFACE
class ExerciseRecommendationResponse(BaseModel):
    """Schema for responding with exercise recommendations."""
    recommended_exercises: list[str] = Field(..., description="List of recommended exercises")
