# app/api/routes/stripe.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession
from app.services.stripe_service import StripeService
from app.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/webhook/")
async def handle_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DatabaseSession
):
    """
    Handle Stripe webhook events for payout status updates.
    """
    # Get raw body and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    try:
        # Verify and construct event
        event = await StripeService.construct_webhook_event(payload, sig_header)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {str(e)}"
        )
    
    # Handle different event types
    if event["type"] == "payout.paid":
        payout_id = event["data"]["object"]["id"]
        background_tasks.add_task(
            WithdrawalService.handle_successful_payout,
            db, payout_id
        )
    
    elif event["type"] == "payout.failed":
        payout_id = event["data"]["object"]["id"]
        background_tasks.add_task(
            WithdrawalService.handle_failed_payout,
            db, payout_id
        )
    
    # Always return 200 to acknowledge receipt
    return {"status": "success"}