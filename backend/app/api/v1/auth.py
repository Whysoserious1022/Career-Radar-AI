from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role="candidate",
        is_active=True,
        is_verified=False
    )
    db.add(user)
    await db.flush()
    
    # Create initial user profile
    profile = UserProfile(
        user_id=user.id,
        full_name=user_in.full_name
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated")

    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
