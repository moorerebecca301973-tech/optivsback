# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status


class UserService:
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_referral_code(db: AsyncSession, referral_code: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.referral_code == referral_code))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate, referrer_id: Optional[uuid.UUID] = None) -> User:
        # Check if user already exists
        if await UserService.get_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        if await UserService.get_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )

        # Generate unique referral code (using part of UUID for simplicity)
        referral_code = str(uuid.uuid4())[:12].replace('-', '').upper()

        # Create user object
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            referral_code=referral_code,
            referrer_id=referrer_id
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update(db: AsyncSession, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_data.model_dump(exclude_unset=True)
        
        # Handle password update separately
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))
        
        # Handle PIN update separately
        if 'pin' in update_data:
            update_data['pin_hash'] = get_password_hash(update_data.pop('pin'))

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        return user
    

    @staticmethod
    async def verify_credentials(db: AsyncSession, identifier: str, password: str) -> Optional[User]:
        """Verify credentials using either username or email"""
        # Try username first
        user = await UserService.get_by_username(db, identifier)
        if not user:
        # If not found by username, try email
            user = await UserService.get_by_email(db, identifier)
    
        if not user:
            return None
    
        if not verify_password(password, user.password_hash):
            return None
    
        return user


    @staticmethod
    async def update_balance(db: AsyncSession, user_id: uuid.UUID, amount: float) -> User:
        """Atomically update user balance. Use negative amount for deductions."""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if deduction would make balance negative
        if user.balance + amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )

        user.balance += amount
        await db.commit()
        await db.refresh(user)
        return user