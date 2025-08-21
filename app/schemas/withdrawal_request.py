# app/schemas/withdrawal_request.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class WithdrawalRequestBase(BaseModel):
    amount: str  # String representation of decimal to avoid floating point issues
    bank_name: str
    account_number: str
    account_name: str

    @validator('amount')
    def validate_amount(cls, v):
        try:
            # Validate it's a positive number that can be converted to Decimal
            amount_decimal = Decimal(v)
            if amount_decimal <= 0:
                raise ValueError('Amount must be greater than zero')
            return v
        except:
            raise ValueError('Invalid amount format')


class WithdrawalRequestCreate(WithdrawalRequestBase):
    user_id: UUID
    pin: str = Field(..., min_length=4, max_length=6, description="User's PIN to authorize withdrawal")


class WithdrawalRequestInDB(WithdrawalRequestBase):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    status: str
    stripe_payout_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WithdrawalRequestResponse(WithdrawalRequestInDB):
    pass