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

@router.post("/webhook/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = "your_webhook_secret_here"
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event (you can add more events)
    if event['type'] == 'checkout.session.completed':
        print("Payment successful!")
    
    return {"status": "success"}

