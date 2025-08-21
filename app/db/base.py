# app/db/base.py
# This file imports all SQLAlchemy models so that Base has knowledge of them.
# This is necessary for Alembic, but even without it, it's good practice for potential future use.

# Import all the models from the 'models' package
from app.db.models.user import User
from app.db.models.transaction import Transaction
from app.db.models.kyc_request import KycRequest
from app.db.models.withdrawal_request import WithdrawalRequest