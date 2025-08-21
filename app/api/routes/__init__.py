# app/api/routes/__init__.py
# Import routes for easy inclusion in main app
from app.api.routes.users import router as users_router
from app.api.routes.withdrawals import router as withdrawals_router
from app.api.routes.stripe import router as stripe_router
from app.api.routes.admin import router as admin_router

__all__ = ["users_router", "withdrawals_router", "stripe_router", "admin_router"]
