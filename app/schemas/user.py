# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# Base properties shared across schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = Field(None, min_length=1, description="Referral code of the user who referred this new user")


# Properties to receive via API on update (all optional)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    pin: Optional[str] = Field(None, min_length=4, max_length=6, description="4-6 digit PIN for withdrawals")


# INITIAL REGISTRATION SCHEMAS (Step 1 & 2)
class UserRegisterInitiate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = Field(None, min_length=1)

class UserRegisterConfirm(UserRegisterInitiate):
    payment_intent_id: str = Field(..., min_length=1)


# Properties stored in DB (includes hashed password and generated fields)
class UserInDB(UserBase):
    id: UUID
    referral_code: str
    referrer_id: Optional[UUID] = None
    balance: float
    role: str
    status: str
    withdrawal_status: str
    is_kyc_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows ORM mode (formerly 'orm_mode')


# Properties to return to client (DO NOT include password hash or other sensitive info)
class UserResponse(UserInDB):
    pass


# Specialized response for login/refresh tokens
class UserWithTokens(UserResponse):
    access_token: str
    refresh_token: Optional[str] = None  # If implementing refresh tokens