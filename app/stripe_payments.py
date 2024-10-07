import stripe
from fastapi import APIRouter, HTTPException
from fastapi import Depends
from .auth import get_current_user

router = APIRouter()

# Stripe API keys (use your actual keys from Stripe dashboard)
stripe.api_key = "your_secret_key_here"

@router.post("/create-checkout-session/")
async def create_checkout_session(current_user: str = Depends(get_current_user)):
    try:
        # Create a checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Minecraft Server Subscription',
                    },
                    'unit_amount': 700,  # 7 dollars in cents
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://yourdomain.com/success',
            cancel_url='https://yourdomain.com/cancel',
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

