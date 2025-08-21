# app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body  # Added Body import
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.api.deps import DatabaseSession, CurrentUser
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserRegisterInitiate, 
    UserRegisterConfirm, UserWithTokens
)
from app.services.user_service import UserService
from app.services.commission_service import CommissionService
from app.services.stripe_service import StripeService
from app.core.security import create_access_token

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register/", status_code=status.HTTP_200_OK)
async def initiate_registration(
    user_data: UserRegisterInitiate,
    db: DatabaseSession
):
    """
    Step 1: Initiate user registration and create Stripe Payment Intent.
    Returns client_secret for frontend to complete payment.
    """
    # Validate user data doesn't already exist
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

    # Validate referral code if provided
    referrer = None
    if user_data.referral_code:
        referrer = await UserService.get_by_referral_code(db, user_data.referral_code)
        if not referrer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid referral code"
            )

    # Create Stripe Payment Intent for £50
    client_secret = await StripeService.create_payment_intent(
        amount=5000  # £50 in pence
    )

    return {"clientSecret": client_secret}


@router.post("/register/confirm/", status_code=status.HTTP_201_CREATED)
async def confirm_registration(
    user_data: UserRegisterConfirm,
    db: DatabaseSession,
    background_tasks: BackgroundTasks
):
    """
    Step 2: Confirm user registration after successful payment.
    Creates user record and distributes referral commissions.
    """
    # Verify Payment Intent was successful
    is_payment_valid = await StripeService.verify_payment_intent(
        user_data.payment_intent_id,
        expected_amount=5000  # £50 in pence
    )
    
    if not is_payment_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsuccessful payment"
        )

    # Find referrer if referral code was provided
    referrer_id = None
    if user_data.referral_code:
        referrer = await UserService.get_by_referral_code(db, user_data.referral_code)
        if referrer:
            referrer_id = referrer.id

    # Create user (this includes all validation)
    user = await UserService.create(db, user_data, referrer_id)

    # Trigger commission distribution in background
    background_tasks.add_task(
        CommissionService.distribute_registration_commission,
        db, user.id
    )

    return {"detail": "User registered successfully"}


@router.post("/login/", response_model=UserWithTokens)
async def login(
    db: DatabaseSession,
    login_identifier: str = Body(..., embed=True, alias="username"),  # Accept both username or email
    password: str = Body(..., embed=True)
):
    """
    Login user and return JWT tokens.
    Accepts either username or email as identifier.
    """
    # Try to find user by username first, then by email
    user = await UserService.get_by_username(db, login_identifier)
    if not user:
        user = await UserService.get_by_email(db, login_identifier)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    access_token = create_access_token(subject=user.username)
    
    return UserWithTokens(
        **user.__dict__,
        access_token=access_token
    )

@router.get("/me/", response_model=UserResponse)
async def read_current_user(current_user: CurrentUser):
    """Get current user information."""
    return current_user


@router.put("/me/", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Update current user information."""
    return await UserService.update(db, current_user.id, user_data)


@router.post("/me/pin/")
async def set_withdrawal_pin(
    db: DatabaseSession,  # Moved to first position
    current_user: CurrentUser,  # Moved to second position
    pin: str = Body(..., min_length=4, max_length=6)  # Default parameter comes last
):
    """Set or update withdrawal PIN."""
    user_data = UserUpdate(pin=pin)
    await UserService.update(db, current_user.id, user_data)
    return {"detail": "PIN updated successfully"}


# Password reset endpoints would go here
# @router.post("/password/reset/request/")
# @router.post("/password/reset/confirm/")