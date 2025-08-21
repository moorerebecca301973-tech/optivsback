# app/schemas/transaction.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class TransactionBase(BaseModel):
    tx_type: str
    amount: float
    status: str
    reference: Optional[str] = None


class TransactionCreate(TransactionBase):
    user_id: UUID


class TransactionInDB(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionResponse(TransactionInDB):
    pass