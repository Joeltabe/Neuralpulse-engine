import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_session_maker, User, UserRole

def get_session():
    return get_session_maker()()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "neuralpulse-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))

security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    error: Optional[str] = None

class UserProfileResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    error: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return user

def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "token_balance": user.token_balance,
        "total_tokens_purchased": user.total_tokens_purchased,
        "total_tokens_used": user.total_tokens_used,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == request.email))
        if result.scalar_one_or_none():
            return AuthResponse(success=False, error="Email already registered")

        hashed = _bcrypt.hashpw(request.password.encode(), _bcrypt.gensalt()).decode()
        user = User(
            email=request.email,
            name=request.name or request.email.split("@")[0],
            password_hash=hashed,
            role=UserRole.free.value,
            token_balance=100,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return AuthResponse(success=True, token=token, user=user_to_dict(user))

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if not user or not _bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
            return AuthResponse(success=False, error="Invalid email or password")

        if not user.is_active:
            return AuthResponse(success=False, error="Account is disabled")

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return AuthResponse(success=True, token=token, user=user_to_dict(user))

@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return UserProfileResponse(success=True, user=user_to_dict(user))

@router.post("/demo-login", response_model=AuthResponse)
async def demo_login():
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == "demo@neuralpulse.ai"))
        demo_user = result.scalar_one_or_none()

        if not demo_user:
            hashed = _bcrypt.hashpw("demo123456".encode(), _bcrypt.gensalt()).decode()
            demo_user = User(
                email="demo@neuralpulse.ai",
                name="Demo User",
                password_hash=hashed,
                role=UserRole.free.value,
                token_balance=500,
            )
            session.add(demo_user)
            await session.commit()
            await session.refresh(demo_user)

        token = create_access_token({"sub": str(demo_user.id), "email": demo_user.email})
        return AuthResponse(success=True, token=token, user=user_to_dict(demo_user))
