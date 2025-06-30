import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import (
    FastAPI, HTTPException, Depends, status, Request, File, UploadFile, Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from passlib.context import CryptContext
import sqlite3

# === CONFIGURATION ===

JWT_SECRET_KEY = "FITPROOF_SUPER_SECRET"  # This should be set from environment in prod!
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours

DB_FILE = os.environ.get(
    "FITNESS_SQLITE_DB",
    "fitness_app.sqlite"
)
UPLOADS_DIR = os.environ.get(
    "UPLOADS_DIR",
    "uploads"
)  # Not used, just informative.

os.makedirs(UPLOADS_DIR, exist_ok=True)

# === FastAPI App Setup ===

app = FastAPI(
    title="Fitness App Backend",
    description=(
        "Backend for fitness proof tracker. Auth, recommendations, proof upload stub, "
        "workout history, and database health."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "User registration and authentication"},
        {"name": "exercise", "description": "Exercise recommendations"},
        {"name": "proof", "description": "Proof (image/video) upload"},
        {"name": "workout", "description": "Workout history"},
        {"name": "health", "description": "Service/DB health checks"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Security & JWT ===

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# PUBLIC_INTERFACE
def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT token for authentication."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=JWT_EXPIRATION_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# PUBLIC_INTERFACE
def verify_password(plain_password, password_hash):
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, password_hash)


# PUBLIC_INTERFACE
def hash_password(password):
    """Hashes a password."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# === Models ===

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, description="Desired username")
    password: str = Field(..., min_length=6, description="Desired password")
    height_cm: float = Field(..., gt=0, description="User's height in centimeters")
    weight_kg: float = Field(..., gt=0, description="User's weight in kilograms")


class UserRegisterResponse(BaseModel):
    username: str
    token: str


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Registered username")
    password: str = Field(..., description="Password for user")


class UserLoginResponse(BaseModel):
    token: str


class ExerciseRecommendRequest(BaseModel):
    height_cm: float = Field(..., gt=0, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")


class ExerciseRecommendation(BaseModel):
    exercise: str
    description: str


class ExerciseRecommendResponse(BaseModel):
    recommendations: List[ExerciseRecommendation]


class ProofUploadResponse(BaseModel):
    message: str
    proof_url: Optional[str] = None


class WorkoutRecord(BaseModel):
    id: int
    timestamp: datetime
    exercise: str
    proof_url: Optional[str]


class WorkoutHistoryResponse(BaseModel):
    workouts: List[WorkoutRecord]


class DBHealthResponse(BaseModel):
    healthy: bool
    message: str


# === Helpers ===

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            height_cm REAL NOT NULL,
            weight_kg REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exercise TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            proof_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


# PUBLIC_INTERFACE
def get_user_by_username(username: str):
    """Fetch a user by username."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    )
    row = cur.fetchone()
    conn.close()
    return row


# PUBLIC_INTERFACE
def authenticate_user(username: str, password: str):
    """Authenticate user and return DB row if authenticated else None."""
    user = get_user_by_username(username)
    if user and verify_password(password, user["hashed_password"]):
        return user
    return None


# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get user for current request based on token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


# === Start up: Create DB tables if needed ===

@app.on_event("startup")
def startup_event():
    init_db()


# === Endpoints ===

# PUBLIC_INTERFACE
@app.post(
    "/auth/register",
    tags=["auth"],
    response_model=UserRegisterResponse,
    summary="Register a new user"
)
def register(data: UserRegisterRequest):
    """
    Register a new user, ensuring username is unique. Returns JWT token on success.
    """
    if get_user_by_username(data.username):
        raise HTTPException(status_code=409, detail="Username already exists.")

    hashed_pw = hash_password(data.password)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, hashed_password, height_cm, weight_kg) "
            "VALUES (?, ?, ?, ?)",
            (data.username, hashed_pw, data.height_cm, data.weight_kg),
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(status_code=500, detail="Registration failed.")
    finally:
        conn.close()

    token = create_jwt_token({"sub": data.username})
    return UserRegisterResponse(username=data.username, token=token)


# PUBLIC_INTERFACE
@app.post(
    "/auth/login",
    tags=["auth"],
    response_model=UserLoginResponse,
    summary="Log in and obtain JWT token"
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Log in using username and password. Returns JWT token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_jwt_token({"sub": user["username"]})
    return UserLoginResponse(token=token)


# PUBLIC_INTERFACE
@app.post(
    "/exercise/recommend",
    tags=["exercise"],
    response_model=ExerciseRecommendResponse,
    summary="Get recommended exercises"
)
def recommend_exercises(
    data: ExerciseRecommendRequest,
    user=Depends(get_current_user)
):
    """
    Recommend suitable exercises based on height and weight.
    Simple BMI check & conditional recommendations for demonstration.
    """
    height_m = data.height_cm / 100
    bmi = data.weight_kg / (height_m ** 2)
    recos: List[ExerciseRecommendation] = []
    if bmi < 18.5:
        recos.append(
            ExerciseRecommendation(
                exercise="Strength Training",
                description=(
                    "Focus on bodyweight and resistance exercises to build muscle mass "
                    "and support healthy weight gain."
                )
            )
        )
        recos.append(
            ExerciseRecommendation(
                exercise="Yoga/Stretching",
                description="Light yoga to improve flexibility and muscle tone."
            )
        )
    elif 18.5 <= bmi < 25:
        recos.append(
            ExerciseRecommendation(
                exercise="Mixed Cardio and Strength",
                description=(
                    "A balanced program with running/cycling "
                    "and resistance training for overall health."
                )
            )
        )
        recos.append(
            ExerciseRecommendation(
                exercise="Core Workouts",
                description="Exercises focusing on strengthening the core muscles."
            )
        )
    else:
        recos.append(
            ExerciseRecommendation(
                exercise="Cardio",
                description=(
                    "Emphasize cardio to help reduce weight: brisk walking, cycling, swimming."
                )
            )
        )
        recos.append(
            ExerciseRecommendation(
                exercise="Circuit Training",
                description="Circuit workouts with short rest intervals."
            )
        )
    return ExerciseRecommendResponse(recommendations=recos)


# PUBLIC_INTERFACE
@app.post(
    "/proof/upload",
    tags=["proof"],
    summary="Upload proof media (image/video)"
)
async def upload_proof(
    request: Request,
    exercise: str = Form(..., description="The exercise performed"),
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    Stub handler for uploading workout proof.
    This endpoint would normally upload media to Cloudinary or other storage, but just simulates this here.
    Stores proof URL (stub) into the workout record.
    """
    # "Save" the file (stub - do NOT actually store for this stub version)
    fake_proof_url = (
        f"https://cloudinary.example.com/user/"
        f"{user['username']}/{file.filename}"
    )
    ts_iso = datetime.utcnow().isoformat()

    # Store record in workouts DB
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO workouts (user_id, exercise, timestamp, proof_url) "
            "VALUES (?, ?, ?, ?)",
            (user["id"], exercise, ts_iso, fake_proof_url)
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(status_code=500, detail="Failed to save workout proof.")
    finally:
        conn.close()

    return ProofUploadResponse(message="Proof uploaded (stub)", proof_url=fake_proof_url)


# PUBLIC_INTERFACE
@app.get(
    "/workout/history",
    tags=["workout"],
    response_model=WorkoutHistoryResponse,
    summary="Get workout history"
)
def get_workout_history(user=Depends(get_current_user)):
    """
    Returns workout history for the authenticated user.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, timestamp, exercise, proof_url FROM workouts
        WHERE user_id = ? ORDER BY timestamp DESC
        """,
        (user["id"],)
    )
    rows = cur.fetchall()
    conn.close()
    history = [
        WorkoutRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            exercise=row["exercise"],
            proof_url=row["proof_url"]
        )
        for row in rows
    ]
    return WorkoutHistoryResponse(workouts=history)


# PUBLIC_INTERFACE
@app.get(
    "/health/db",
    tags=["health"],
    response_model=DBHealthResponse,
    summary="Health: Check database healthy"
)
def db_health_check():
    """
    Check health/connection of the SQLite database.
    Returns true if connection and SELECT 1 succeed.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return DBHealthResponse(healthy=True, message="DB connection OK.")
    except Exception as exc:
        msg = f"Database error: {exc}"
        return DBHealthResponse(
            healthy=False,
            message=msg
        )


# Swagger-Help for the WebSocket (not implemented, just a stub for docs compliance)
@app.get("/", tags=["health"])
def health_check():
    """Basic service health check."""
    return {"message": "Healthy"}


# Make sure generated OpenAPI covers form-data, auth, and all tags for frontend integration.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
