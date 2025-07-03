from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router

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

@app.get("/")
def health_check():
    return {"message": "Healthy"}
