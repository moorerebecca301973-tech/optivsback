# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional, Annotated
from app.core.config import settings
from app.core.security import verify_password
from app.db.session import get_db
from app.db.models.user import User
from app.services.user_service import UserService

# HTTP Bearer scheme for JWT tokens
oauth2_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from "Bearer <token>"
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await UserService.get_by_username(db, username) or await UserService.get_by_email(db, username)
    if user is None:
        raise credentials_exception
    
    # Check if user account is active
    if user.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency that ensures the current user is active.
    This is redundant with get_current_user now but kept for clarity and future use.
    """
    return current_user


# Type annotations for use in route dependencies
CurrentUser = Annotated[User, Depends(get_current_active_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


# Optional: Admin role dependency
async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency that requires the current user to be an admin.
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


AdminUser = Annotated[User, Depends(get_current_admin)]