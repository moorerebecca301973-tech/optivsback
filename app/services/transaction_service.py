# app/services/transaction_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate
from typing import Optional
import uuid


class TransactionService:
    
    @staticmethod
    async def create(db: AsyncSession, transaction_data: TransactionCreate) -> Transaction:
        db_transaction = Transaction(**transaction_data.model_dump())
        db.add(db_transaction)
        await db.commit()
        await db.refresh(db_transaction)
        return db_transaction

    @staticmethod
    async def create_commission(db: AsyncSession, user_id: uuid.UUID, amount: float, reference: str) -> Transaction:
        """Helper to create a commission transaction."""
        transaction_data = TransactionCreate(
            user_id=user_id,
            tx_type="commission",
            amount=amount,
            status="completed",
            reference=reference
        )
        return await TransactionService.create(db, transaction_data)

    @staticmethod
    async def create_withdrawal_transaction(db: AsyncSession, user_id: uuid.UUID, amount: float) -> Transaction:
        """Helper to create a withdrawal transaction (negative amount)."""
        transaction_data = TransactionCreate(
            user_id=user_id,
            tx_type="withdrawal",
            amount=-amount,  # Negative amount for withdrawal
            status="processing",  # Starts as processing, updated by webhook
            reference="Withdrawal request"
        )
        return await TransactionService.create(db, transaction_data)

    @staticmethod
    async def update_status(db: AsyncSession, transaction_id: uuid.UUID, status: str) -> Optional[Transaction]:
        transaction = await db.get(Transaction, transaction_id)
        if transaction:
            transaction.status = status
            await db.commit()
            await db.refresh(transaction)
        return transaction