# app/api/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException, status ,Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid

from app.api.deps import DatabaseSession, AdminUser
from app.db.models.user import User
from app.db.models.transaction import Transaction
from app.db.models.kyc_request import KycRequest
from app.db.models.withdrawal_request import WithdrawalRequest
from app.schemas.user import UserResponse
from app.schemas.kyc_request import KycRequestResponse, KycRequestUpdate
from app.schemas.withdrawal_request import WithdrawalRequestResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    db: DatabaseSession,
    admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    search: Optional[str] = None
):
    """Get list of all users with optional filtering."""
    query = select(User)
    
    if status_filter:
        query = query.where(User.status == status_filter)
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.first_name.ilike(f"%{search}%")) |
            (User.last_name.ilike(f"%{search}%"))
        )
    
    result = await db.execute(
        query.order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    users = result.scalars().all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: uuid.UUID,
    db: DatabaseSession,
    admin: AdminUser
):
    """Get detailed information about a specific user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: uuid.UUID,
    db: DatabaseSession,
    admin: AdminUser,
    status: str = Body(..., embed=True)
):
    """Update user account status (active/frozen)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if status not in ['active', 'frozen']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'active' or 'frozen'"
        )
    
    user.status = status
    await db.commit()
    await db.refresh(user)
    
    return {"detail": f"User status updated to {status}"}


@router.get("/withdrawals/", response_model=List[WithdrawalRequestResponse])
async def list_withdrawals(
    db: DatabaseSession,
    admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None
):
    """Get list of all withdrawal requests for monitoring."""
    query = select(WithdrawalRequest)
    
    if status_filter:
        query = query.where(WithdrawalRequest.status == status_filter)
    
    result = await db.execute(
        query.order_by(WithdrawalRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    withdrawals = result.scalars().all()
    return withdrawals


@router.get("/kyc-requests/", response_model=List[KycRequestResponse])
async def list_kyc_requests(
    db: DatabaseSession,
    admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None
):
    """Get list of all KYC requests for review."""
    query = select(KycRequest)
    
    if status_filter:
        query = query.where(KycRequest.status == status_filter)
    
    result = await db.execute(
        query.order_by(KycRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    kyc_requests = result.scalars().all()
    return kyc_requests


@router.patch("/kyc-requests/{request_id}", response_model=KycRequestResponse)
async def review_kyc_request(
    request_id: uuid.UUID,
    kyc_update: KycRequestUpdate,
    db: DatabaseSession,
    admin: AdminUser
):
    """Review and update KYC request status."""
    kyc_request = await db.get(KycRequest, request_id)
    if not kyc_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC request not found"
        )
    
    if kyc_request.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC request has already been reviewed"
        )
    
    # Update status
    kyc_request.status = kyc_update.status
    
    # Set rejection reason if provided and status is rejected
    if kyc_update.status == 'rejected' and kyc_update.rejection_reason:
        kyc_request.rejection_reason = kyc_update.rejection_reason
    
    # If approved, mark user as KYC verified
    if kyc_update.status == 'approved':
        user = await db.get(User, kyc_request.user_id)
        if user:
            user.is_kyc_verified = True
    
    await db.commit()
    await db.refresh(kyc_request)
    
    return kyc_request


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: DatabaseSession,
    admin: AdminUser
):
    """Get admin dashboard statistics."""
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()
    
    # Active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == 'active')
    )
    active_users = active_users_result.scalar()
    
    # Total transactions volume
    total_volume_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
    )
    total_volume = total_volume_result.scalar()
    
    # Pending withdrawals
    pending_withdrawals_result = await db.execute(
        select(func.count(WithdrawalRequest.id)).where(
            WithdrawalRequest.status == 'processing'
        )
    )
    pending_withdrawals = pending_withdrawals_result.scalar()
    
    # Pending KYC requests
    pending_kyc_result = await db.execute(
        select(func.count(KycRequest.id)).where(KycRequest.status == 'pending')
    )
    pending_kyc = pending_kyc_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_volume": float(total_volume),
        "pending_withdrawals": pending_withdrawals,
        "pending_kyc_requests": pending_kyc
    }