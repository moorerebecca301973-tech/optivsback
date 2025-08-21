# app/db/models/withdrawal_request.py
from sqlalchemy import Column, String, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel

class WithdrawalRequest(BaseModel):
    __tablename__ = "withdrawal_requests"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True # Enforces one-to-one relationship with Transaction
    )
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default='processing') # 'processing', 'paid', 'failed', 'requires_action'
    bank_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    account_name = Column(String, nullable=False)
    stripe_payout_id = Column(String, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="withdrawal_requests")
    transaction = relationship("Transaction", back_populates="withdrawal_request")

    # Index on status for filtering in admin panel
    __table_args__ = (
        Index('ix_withdrawal_requests_status', 'status'),
    )