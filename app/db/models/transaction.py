# app/db/models/transaction.py
from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel

class Transaction(BaseModel):
    __tablename__ = "transactions"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tx_type = Column(String, nullable=False) # 'commission', 'withdrawal', 'bonus'
    reference = Column(String, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default='pending') # 'pending', 'completed', 'failed', 'processing'

    # Relationship to User
    user = relationship("User", back_populates="transactions", foreign_keys=[user_id])
    # Relationship to WithdrawalRequest (one-to-one)
    withdrawal_request = relationship("WithdrawalRequest", back_populates="transaction", uselist=False)