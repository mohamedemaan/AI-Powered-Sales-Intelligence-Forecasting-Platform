from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
import os
try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_key")
except ImportError:
    stripe = None

router = APIRouter()

@router.post("/create-checkout-session")
def create_checkout(tenant_id: str, plan_type: str):
    '''
    Generates a Stripe Checkout URL for upgrades.
    '''
    plan_prices = {
        "PRO": "price_pro_mock_123",
        "BUSINESS": "price_biz_mock_456"
    }
    
    if plan_type not in plan_prices:
        raise HTTPException(status_code=400, detail="Invalid Plan")
        
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan_prices[plan_type],
                'quantity': 1,
            }],
            mode='subscription',
            success_url="https://yourdomain.com/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://yourdomain.com/pricing",
            client_reference_id=tenant_id
        )
        return {"checkout_url": session.url}
    except Exception as e:
        return {"error": str(e)}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    '''
    Handles async payment success/failure events.
    '''
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # In production, verify signature:
    # event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    
    # Mocking event parsing:
    event = {"type": "checkout.session.completed", "data": {"object": {"client_reference_id": "tenant_123"}}}
    
    if event["type"] == "checkout.session.completed":
        tenant_id = event["data"]["object"]["client_reference_id"]
        # Update tenant status in DB...
        pass
        
    return {"status": "success"}
