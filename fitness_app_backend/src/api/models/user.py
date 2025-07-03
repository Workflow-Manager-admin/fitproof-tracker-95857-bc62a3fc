"""User SQLAlchemy model and related Pydantic schemas for the Fitness App."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr, Field

Base = declarative_base()

class User(Base):
    """Database user model."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

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

    class Config:
        orm_mode = True
