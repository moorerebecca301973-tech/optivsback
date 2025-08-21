# app/schemas/kyc_request.py
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID


class KycRequestBase(BaseModel):
    document_front_url: HttpUrl
    document_back_url: Optional[HttpUrl] = None
    selfie_url: HttpUrl


class KycRequestCreate(KycRequestBase):
    user_id: UUID


class KycRequestUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None


class KycRequestInDB(KycRequestBase):
    id: UUID
    user_id: UUID
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KycRequestResponse(KycRequestInDB):
    pass