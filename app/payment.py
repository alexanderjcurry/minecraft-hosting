from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import stripe
from .models import User, Payment
from auth import get_current_user
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from plans import plans

stripe.api_key = STRIPE_SECRET_KEY
router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(plan_id: str, request: Request, user: User = Depends(get_current_user)):
    if plan_id not in plans:
        raise HTTPException(status_code=400, detail="Invalid plan ID.")
    
    plan = plans[plan_id]
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': plan['price_id'],
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.url_for('payment_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.url_for('payment_cancel'),
            metadata={
                'user_id': str(user.id),
                'plan_id': plan_id,
            },
        )
        return {"sessionId": checkout_session['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/payment-success')
async def payment_success(session_id: str):
    return JSONResponse({"message": "Payment successful!", "session_id": session_id})

@router.get('/payment-cancel')
async def payment_cancel():
    return JSONResponse({"message": "Payment canceled."})

@router.post('/webhook')
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_session(session)

    return {"status": "success"}

async def handle_checkout_session(session):
    user_id = session['metadata']['user_id']
    plan_id = session['metadata']['plan_id']

    # Fetch user and record payment
    user = await User.get(id=user_id)
    payment = Payment(user_id=user_id, plan_id=plan_id, amount=session['amount_total'] / 100, currency=session['currency'], payment_status='paid', stripe_session_id=session['id'])
    await payment.save()
    await create_minecraft_server(user, plan_id)

