from database import User, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from .dependencies import get_current_user
from .models import Token, UserCreate, UserLogin, UserResponse
from .utils import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Client = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    response = (
        db.table("users").select("*").eq("username", user_data.username).execute()
    )
    if response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    # Create new user object to generate ID and hash password
    hashed_password = get_password_hash(user_data.password)
    new_user_obj = User(username=user_data.username, hashed_password=hashed_password)

    user_dict = {
        "id": new_user_obj.id,
        "username": new_user_obj.username,
        "hashed_password": new_user_obj.hashed_password,
        "created_at": new_user_obj.created_at.isoformat(),
    }

    # Insert into Supabase
    insert_response = db.table("users").insert(user_dict).execute()

    if not insert_response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    return user_dict


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Client = Depends(get_db)):
    """Login and get access token"""
    # Find user by username
    response = (
        db.table("users").select("*").eq("username", user_data.username).execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data_db = response.data[0]

    # Verify password
    if not verify_password(user_data.password, user_data_db["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user_data_db["id"], "username": user_data_db["username"]}
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
