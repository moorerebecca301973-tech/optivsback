# app/services/withdrawal_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.db.models.transaction import Transaction
from app.db.models.withdrawal_request import WithdrawalRequest
from app.schemas.withdrawal_request import WithdrawalRequestCreate
from app.services.user_service import UserService
from app.services.transaction_service import TransactionService
from app.services.stripe_service import StripeService
from app.core.security import verify_password
from fastapi import HTTPException, status
import uuid
from decimal import Decimal


class WithdrawalService:
    
    @staticmethod
    async def validate_withdrawal_request(db: AsyncSession, user_id: uuid.UUID, amount: float, pin: str) -> User:
        """Validate all conditions for a withdrawal request."""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check KYC verification
        if not user.is_kyc_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC verification required for withdrawals"
            )
        
        # Check withdrawal status
        if user.withdrawal_status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Withdrawals are currently paused for your account"
            )
        
        # Check sufficient balance
        if user.balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        
        # Verify PIN
        if not user.pin_hash or not verify_password(pin, user.pin_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PIN"
            )
        
        return user

    @staticmethod
    async def create_withdrawal(
        db: AsyncSession, 
        withdrawal_data: WithdrawalRequestCreate,
        user_id: uuid.UUID
    ) -> WithdrawalRequest:
        """
        Create a withdrawal request with full validation and Stripe integration.
        This is the main withdrawal workflow.
        """
        amount_decimal = Decimal(withdrawal_data.amount)
        
        # Validate the withdrawal request
        user = await WithdrawalService.validate_withdrawal_request(
            db, user_id, float(amount_decimal), withdrawal_data.pin
        )
        
        # Start database transaction
        async with db.begin():
            try:
                # 1. Create withdrawal transaction (negative amount)
                transaction = await TransactionService.create_withdrawal_transaction(
                    db, user_id, float(amount_decimal)
                )
                
                # 2. Immediately deduct from user balance
                await UserService.update_balance(db, user_id, -float(amount_decimal))
                
                # 3. Create bank account token with Stripe
                # Note: For UK banks, we need sort_code + account_number
                # You might need to adjust this based on your country's banking format
                bank_token = await StripeService.create_bank_account_token(
                    account_number=withdrawal_data.account_number,
                    sort_code="000000",  # Placeholder - you'll need to collect sort_code or adjust for your country
                    account_name=withdrawal_data.account_name
                )
                
                # 4. Create Stripe payout
                payout_id = await StripeService.create_payout(
                    amount=int(amount_decimal * 100),  # Convert to pence
                    bank_token=bank_token,
                    description=f"Withdrawal for user {user.username}"
                )
                
                # 5. Create withdrawal request record
                db_withdrawal = WithdrawalRequest(
                    user_id=user_id,
                    transaction_id=transaction.id,
                    amount=float(amount_decimal),
                    bank_name=withdrawal_data.bank_name,
                    account_number=withdrawal_data.account_number,
                    account_name=withdrawal_data.account_name,
                    stripe_payout_id=payout_id
                )
                
                db.add(db_withdrawal)
                await db.commit()
                await db.refresh(db_withdrawal)
                await db.refresh(transaction)
                
                return db_withdrawal
                
            except Exception as e:
                await db.rollback()
                # Re-raise the exception to be handled by the API layer
                raise e

    @staticmethod
    async def handle_successful_payout(db: AsyncSession, payout_id: str) -> None:
        """Update records when a payout is successful."""
        async with db.begin():
            # Find the withdrawal request
            result = await db.execute(
                select(WithdrawalRequest).where(WithdrawalRequest.stripe_payout_id == payout_id)
            )
            withdrawal_request = result.scalar_one_or_none()
            
            if withdrawal_request:
                withdrawal_request.status = 'paid'
                # Update the associated transaction status
                await TransactionService.update_status(
                    db, withdrawal_request.transaction_id, 'completed'
                )
                await db.commit()

    @staticmethod
    async def handle_failed_payout(db: AsyncSession, payout_id: str) -> None:
        """Handle failed payout by refunding user balance and updating records."""
        async with db.begin():
            # Find the withdrawal request
            result = await db.execute(
                select(WithdrawalRequest).where(WithdrawalRequest.stripe_payout_id == payout_id)
            )
            withdrawal_request = result.scalar_one_or_none()
            
            if withdrawal_request:
                withdrawal_request.status = 'failed'
                
                # Update transaction status
                await TransactionService.update_status(
                    db, withdrawal_request.transaction_id, 'failed'
                )
                
                # Refund the amount to user's balance
                await UserService.update_balance(
                    db, withdrawal_request.user_id, withdrawal_request.amount
                )
                
                await db.commit()