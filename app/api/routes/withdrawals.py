# app/api/routes/withdrawals.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.api.deps import DatabaseSession, CurrentUser
from app.schemas.withdrawal_request import WithdrawalRequestCreate, WithdrawalRequestResponse
from app.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])


@router.post("/", response_model=WithdrawalRequestResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_withdrawal(
    withdrawal_data: WithdrawalRequestCreate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Create a new withdrawal request.
    Immediately deducts balance and initiates Stripe payout.
    """
    # The service handles all validation and Stripe integration
    withdrawal_request = await WithdrawalService.create_withdrawal(
        db, withdrawal_data, current_user.id
    )
    
    return withdrawal_request


@router.get("/", response_model=List[WithdrawalRequestResponse])
async def get_user_withdrawals(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    """Get current user's withdrawal history."""
    from sqlalchemy import select
    from app.db.models.withdrawal_request import WithdrawalRequest
    
    result = await db.execute(
        select(WithdrawalRequest)
        .where(WithdrawalRequest.user_id == current_user.id)
        .order_by(WithdrawalRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    withdrawals = result.scalars().all()
    return withdrawals


@router.get("/{withdrawal_id}", response_model=WithdrawalRequestResponse)
async def get_withdrawal(
    withdrawal_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get specific withdrawal details."""
    from sqlalchemy import select
    from app.db.models.withdrawal_request import WithdrawalRequest
    
    result = await db.execute(
        select(WithdrawalRequest)
        .where(
            (WithdrawalRequest.id == withdrawal_id) &
            (WithdrawalRequest.user_id == current_user.id)
        )
    )
    
    withdrawal = result.scalar_one_or_none()
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Withdrawal not found"
        )
    
    return withdrawal