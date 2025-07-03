"""FastAPI endpoints for authentication: register and login."""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.api.models.user import User as UserModel, UserCreate, UserLogin, UserRead
from src.api.dependencies import get_db, get_password_hash, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# PUBLIC_INTERFACE
@router.post("/register", response_model=UserRead, summary="Register new user", description="Register a new user with email and password.")
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with hashed password."""
    user_exist = db.query(UserModel).filter(UserModel.email == user_create.email).first()
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    hashed = get_password_hash(user_create.password)
    db_user = UserModel(email=user_create.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# PUBLIC_INTERFACE
@router.post("/login", summary="Login user", description="Authenticate user and issue JWT.")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT if successful."""
    user = db.query(UserModel).filter(UserModel.email == user_login.email).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
