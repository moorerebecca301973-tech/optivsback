# app/db/models/kyc_request.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel

class KycRequest(BaseModel):
    __tablename__ = "kyc_requests"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(String, nullable=False, default='pending') # 'pending', 'approved', 'rejected'
    rejection_reason = Column(String, nullable=True)
    document_front_url = Column(String, nullable=False)
    document_back_url = Column(String, nullable=True)
    selfie_url = Column(String, nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="kyc_requests")