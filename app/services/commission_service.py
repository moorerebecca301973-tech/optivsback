# app/services/commission_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.services.user_service import UserService
from app.services.transaction_service import TransactionService
from typing import List
import uuid


class CommissionService:
    # Commission rates for each level (level 1 = direct referrer, level 2 = referrer's referrer, etc.)
    COMMISSION_RATES = [0.50, 0.25, 0.15, 0.05, 0.03, 0.02]  # 50%, 25%, 15%, 5%, 3%, 2%
    REGISTRATION_FEE = 50.00  # £50 registration fee

    @staticmethod
    async def distribute_registration_commission(db: AsyncSession, new_user_id: uuid.UUID) -> None:
        """
        Distribute commission to upline users when a new user registers and pays.
        This is the core business logic algorithm.
        """
        new_user = await UserService.get_by_id(db, new_user_id)
        if not new_user or not new_user.referrer_id:
            return  # No referrer, no commission to distribute

        current_user_id = new_user.referrer_id
        distributed_levels = 0

        # Traverse up the referral chain (max 6 levels)
        while current_user_id and distributed_levels < len(CommissionService.COMMISSION_RATES):
            referrer = await UserService.get_by_id(db, current_user_id)
            if not referrer:
                break  # Referrer doesn't exist (shouldn't happen normally)

            # Calculate commission for this level
            commission_rate = CommissionService.COMMISSION_RATES[distributed_levels]
            commission_amount = CommissionService.REGISTRATION_FEE * commission_rate

            # Create commission transaction for the referrer
            await TransactionService.create_commission(
                db=db,
                user_id=referrer.id,
                amount=commission_amount,
                reference=f"Commission from Level {distributed_levels + 1} referral: {new_user.username}"
            )

            # Update referrer's balance
            await UserService.update_balance(db, referrer.id, commission_amount)

            # Move to next level in the chain
            current_user_id = referrer.referrer_id
            distributed_levels += 1