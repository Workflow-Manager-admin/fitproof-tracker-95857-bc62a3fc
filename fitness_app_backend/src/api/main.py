from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router
from src.api.routers.profile_and_recommend import router as profile_and_recommend_router
from src.api.routers.proof import router as proof_router
from src.api.routers.history import router as history_router

from src.api.dependencies import engine
from src.api.models.user import Base as UserBase
from src.api.models.history import WorkoutSession  # Import to ensure table exists

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database (create tables if not exist)
UserBase.metadata.create_all(bind=engine)
WorkoutSession.metadata.create_all(bind=engine)  # Ensure workout_sessions table

app.include_router(auth_router)
app.include_router(profile_and_recommend_router)
app.include_router(proof_router)
app.include_router(history_router)


@app.get("/")
def health_check():
    return {"message": "Healthy"}
