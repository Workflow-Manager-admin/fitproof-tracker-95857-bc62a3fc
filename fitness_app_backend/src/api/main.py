from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router
from src.api.routers.profile_and_recommend import router as profile_and_recommend_router
from src.api.routers.proof import router as proof_router

from src.api.dependencies import engine
from src.api.models.user import Base as UserBase

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

app.include_router(auth_router)
app.include_router(profile_and_recommend_router)
app.include_router(proof_router)


@app.get("/")
def health_check():
    return {"message": "Healthy"}
