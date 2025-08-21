# app/db/models/user.py
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel

class User(BaseModel):
    # Override automatic table name generation for this specific model
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    referral_code = Column(String, unique=True, index=True, nullable=False)
    # ForeignKey to 'users.id' - this is a self-referential relationship
    referrer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    role = Column(String, nullable=False, default='user') # 'user', 'admin'
    status = Column(String, nullable=False, default='active') # 'active', 'frozen'
    withdrawal_status = Column(String, nullable=False, default='active') # 'active', 'paused'
    is_kyc_verified = Column(Boolean, nullable=False, default=False)
    pin_hash = Column(String, nullable=True)

    # Define the relationship for referrer (the user who referred this user)
    referrer = relationship("User", remote_side="User.id", backref="referred_users", post_update=True)
    # Define relationships to other tables (will be used from the other side)
    transactions = relationship("Transaction", back_populates="user", foreign_keys="Transaction.user_id")
    kyc_requests = relationship("KycRequest", back_populates="user")
    withdrawal_requests = relationship("WithdrawalRequest", back_populates="user")

    # Add a composite index if we often query by both status and withdrawal_status, for example
    __table_args__ = (
        Index('ix_users_status_withdrawal', 'status', 'withdrawal_status'),
    )