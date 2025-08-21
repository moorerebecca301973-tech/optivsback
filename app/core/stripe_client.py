# app/core/stripe_client.py
import stripe
from app.core.config import settings

# Configure the Stripe SDK with the secret key
stripe.api_key = settings.STRIPE_SECRET_KEY
# Optional: For better error handling, you can set the API version
# stripe.api_version = "2023-10-16"