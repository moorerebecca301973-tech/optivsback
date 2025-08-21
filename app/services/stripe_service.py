# app/services/stripe_service.py
import stripe
from app.core.config import settings
from app.core.stripe_client import stripe
from fastapi import HTTPException, status
from typing import Dict, Any


class StripeService:
    
    @staticmethod
    async def create_payment_intent(amount: int, currency: str = "gbp") -> str:
        """Create a PaymentIntent for user registration."""
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,  # in smallest currency unit (pence)
                currency=currency,
                automatic_payment_methods={"enabled": True},
                metadata={"purpose": "user_registration"}
            )
            return payment_intent.client_secret
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def verify_payment_intent(payment_intent_id: str, expected_amount: int) -> bool:
        """Verify that a PaymentIntent was successful and for the correct amount."""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return (
                payment_intent.status == "succeeded" and
                payment_intent.amount == expected_amount and
                payment_intent.currency == "gbp"
            )
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment intent: {str(e)}"
            )

    @staticmethod
    async def create_bank_account_token(account_number: str, sort_code: str, account_name: str) -> str:
        """Create a Stripe token for bank account details (PCI-compliant)."""
        try:
            # UK bank accounts use sort_code + account_number
            # Format: sort_code (6 digits) and account_number (8 digits)
            token = stripe.Token.create(
                bank_account={
                    "country": "GB",
                    "currency": "gbp",
                    "account_holder_name": account_name,
                    "account_holder_type": "individual",
                    "account_number": account_number,
                    "sort_code": sort_code,
                }
            )
            return token.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bank account details: {str(e)}"
            )

    @staticmethod
    async def create_payout(amount: int, bank_token: str, description: str = "") -> str:
        """Create a Stripe Payout to a bank account."""
        try:
            payout = stripe.Payout.create(
                amount=amount,
                currency="gbp",
                method="standard",
                destination=bank_token,
                description=description or f"Withdrawal payout {amount} GBP"
            )
            return payout.id  # Returns payout ID like "po_..."
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe payout failed: {str(e)}"
            )

    @staticmethod
    async def construct_webhook_event(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify and construct a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {str(e)}"
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Webhook signature verification failed: {str(e)}"
            )