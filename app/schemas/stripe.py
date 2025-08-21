# app/schemas/stripe.py
from pydantic import BaseModel
from typing import Any, Optional


class StripeWebhookEvent(BaseModel):
    """Schema for the raw data we receive from Stripe webhooks."""
    id: str
    type: str
    data: dict[str, Any]  # The nested object structure can be parsed based on 'type'
    created: Optional[int] = None

    class Config:
        # We want to be lenient and accept any extra fields Stripe might send
        extra = 'ignore'