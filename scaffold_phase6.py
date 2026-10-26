import os

saas_files = {
    "backend/app/models/tenant.py": """from sqlalchemy import Column, String, Integer, Boolean
from app.db.base import BaseModel

class Tenant(BaseModel):
    __tablename__ = "tenants"
    name = Column(String(255), nullable=False)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    subscription_tier = Column(String(50), default="FREE") # FREE, PRO, BUSINESS, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")
    current_period_end = Column(String(50))
    api_calls_count = Column(Integer, default=0)
    forecasts_count = Column(Integer, default=0)
    
    # In a full implementation, all other models (User, Product, etc.) 
    # would receive a tenant_id = Column(UUID, ForeignKey("tenants.id"))
""",

    "backend/app/services/billing.py": """import logging

logger = logging.getLogger(__name__)

# Mocked Plan Limits
PLAN_LIMITS = {
    "FREE": {"users": 1, "forecasts": 10, "api_calls": 1000},
    "PRO": {"users": 5, "forecasts": 100, "api_calls": 50000},
    "BUSINESS": {"users": 20, "forecasts": 1000, "api_calls": 500000},
    "ENTERPRISE": {"users": float('inf'), "forecasts": float('inf'), "api_calls": float('inf')}
}

def check_usage_limits(tenant, feature: str) -> bool:
    '''
    Enforces SaaS feature gating and usage limits.
    '''
    limits = PLAN_LIMITS.get(tenant.subscription_tier, PLAN_LIMITS["FREE"])
    
    if feature == "forecasts":
        return tenant.forecasts_count < limits["forecasts"]
    elif feature == "api_calls":
        return tenant.api_calls_count < limits["api_calls"]
        
    return True

def record_usage(tenant, feature: str, amount: int = 1):
    '''
    Increments usage counters for the tenant.
    '''
    if feature == "forecasts":
        tenant.forecasts_count += amount
    elif feature == "api_calls":
        tenant.api_calls_count += amount
""",

    "backend/app/api/v1/endpoints/billing.py": """from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db
import stripe
import os

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_key")

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
""",

    "backend/app/services/email.py": """import logging

logger = logging.getLogger(__name__)

def send_onboarding_email(email: str, name: str):
    '''
    Sends a welcome sequence to activate new signups.
    Uses tools like Resend or SendGrid in production.
    '''
    logger.info(f"Sending Onboarding Email to {email}")
    # mock_resend.emails.send(...)

def send_alert_email(email: str, alert_type: str, details: str):
    '''
    Transactional email for anomalies or stock-outs.
    '''
    logger.info(f"Alert [{alert_type}] sent to {email}")
""",

    "frontend/app/landing/page.tsx": """import React from 'react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="flex justify-between items-center p-6 max-w-6xl mx-auto">
        <div className="text-2xl font-bold tracking-tight text-white">SalesIntel<span className="text-blue-500">.ai</span></div>
        <div className="space-x-8 text-sm font-medium">
          <a href="#features" className="hover:text-blue-400 transition-colors">Features</a>
          <a href="#pricing" className="hover:text-blue-400 transition-colors">Pricing</a>
          <a href="/login" className="hover:text-blue-400 transition-colors">Sign In</a>
          <a href="/register" className="bg-blue-600 px-5 py-2.5 rounded-full hover:bg-blue-500 transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]">Get Started</a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-4xl mx-auto text-center pt-32 pb-20">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
          Predict demand.<br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            Never stock out again.
          </span>
        </h1>
        <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          The autonomous Sales Intelligence Platform that learns your business, spots anomalies, and makes inventory decisions before you even realize there's a problem.
        </p>
        <div className="flex justify-center gap-4">
          <button className="bg-blue-600 text-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-blue-500 transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)] hover:-translate-y-1">
            Start Free Trial
          </button>
          <button className="bg-slate-800 text-white px-8 py-4 rounded-full text-lg font-semibold border border-slate-700 hover:bg-slate-700 transition-all">
            Book a Demo
          </button>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="max-w-6xl mx-auto py-24 px-6">
        <h2 className="text-3xl font-bold text-center mb-16">Simple, Usage-based Pricing</h2>
        <div className="grid md:grid-cols-3 gap-8">
          
          {/* Free Tier */}
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h3 className="text-xl font-semibold mb-2">Starter</h3>
            <div className="text-4xl font-bold mb-6">$0<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 1 User Seat</li>
              <li>✓ 10 ML Forecasts/mo</li>
              <li>✓ 7-Day Data History</li>
            </ul>
            <button className="w-full py-3 rounded-lg border border-slate-600 hover:bg-slate-700 transition-colors">Current Plan</button>
          </div>

          {/* Pro Tier */}
          <div className="bg-gradient-to-b from-blue-900/50 to-slate-800 p-8 rounded-2xl border border-blue-500/50 relative transform md:-translate-y-4">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold">Most Popular</div>
            <h3 className="text-xl font-semibold mb-2">Pro</h3>
            <div className="text-4xl font-bold mb-6">$49<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 5 User Seats</li>
              <li>✓ 100 ML Forecasts/mo</li>
              <li>✓ AI Copilot Access</li>
              <li>✓ Slack Alerts</li>
            </ul>
            <button className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 font-medium transition-colors">Upgrade to Pro</button>
          </div>

          {/* Business Tier */}
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h3 className="text-xl font-semibold mb-2">Business</h3>
            <div className="text-4xl font-bold mb-6">$199<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 20 User Seats</li>
              <li>✓ Unlimited Forecasts</li>
              <li>✓ Custom Model Retraining</li>
              <li>✓ Priority Support</li>
            </ul>
            <button className="w-full py-3 rounded-lg border border-slate-600 hover:bg-slate-700 transition-colors">Contact Sales</button>
          </div>

        </div>
      </section>
    </div>
  )
}
""",

    "frontend/app/onboarding/page.tsx": """export default function Onboarding() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
      <div className="bg-slate-800 max-w-lg w-full p-10 rounded-2xl border border-slate-700 text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Welcome to SalesIntel.ai</h2>
        <p className="text-slate-400 mb-8">Let's get your autonomous intelligence engine running.</p>
        
        <div className="space-y-4">
          <button className="w-full bg-blue-600 text-white py-4 rounded-xl font-medium hover:bg-blue-500 transition-all flex items-center justify-center gap-2">
            Upload Historical Sales Data (CSV)
          </button>
          <button className="w-full bg-slate-700 text-white py-4 rounded-xl font-medium hover:bg-slate-600 transition-all">
            Connect Shopify Integration
          </button>
        </div>
        
        <a href="/dashboard" className="block mt-6 text-sm text-slate-500 hover:text-white transition-colors">Skip for now, show me the demo dashboard</a>
      </div>
    </div>
  )
}
"""
}

def create_phase6():
    for filepath, content in saas_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Update API Router for Billing
    api_path = "backend/app/api/v1/api.py"
    if os.path.exists(api_path):
        with open(api_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "endpoints import billing" not in content:
            with open(api_path, "w", encoding='utf-8') as f:
                new_content = content.replace(
                    "from app.api.v1.endpoints import auth, users, products, orders, data, ml",
                    "from app.api.v1.endpoints import auth, users, products, orders, data, ml, billing"
                )
                new_content += "api_router.include_router(billing.router, prefix='/billing', tags=['billing'])\\n"
                f.write(new_content)

if __name__ == "__main__":
    create_phase6()
    print("Phase 6 setup (SaaS, Stripe, Multi-Tenancy, Marketing) completed successfully!")
