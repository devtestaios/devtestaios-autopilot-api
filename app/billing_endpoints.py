"""
Stripe Integration for PulseBridge.ai
Backend payment processing endpoints
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import stripe
import os
import json
import logging
from datetime import datetime, timedelta

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe.api_version = '2024-11-20.acacia'

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

logger = logging.getLogger(__name__)

# Pydantic models
class CreateCheckoutRequest(BaseModel):
    price_id: str
    company_id: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CreatePortalRequest(BaseModel):
    company_id: str
    return_url: Optional[str] = None

class SubscriptionStatusResponse(BaseModel):
    subscription_id: Optional[str]
    status: str
    current_period_end: Optional[datetime]
    subscription_tier: str
    trial_end: Optional[datetime]
    customer_id: Optional[str]

# Stripe Price IDs (set these in environment variables)
PRICE_IDS = {
    'solo_professional': os.getenv('STRIPE_PRICE_SOLO_MONTHLY'),
    'growth_team': os.getenv('STRIPE_PRICE_GROWTH_MONTHLY'), 
    'professional_agency': os.getenv('STRIPE_PRICE_PROFESSIONAL_MONTHLY'),
    'enterprise': os.getenv('STRIPE_PRICE_ENTERPRISE_MONTHLY'),
    'enterprise_plus': os.getenv('STRIPE_PRICE_ENTERPRISE_PLUS_MONTHLY')
}

@router.post("/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create Stripe checkout session for subscription
    """
    try:
        # Get company info from database (you'll need to implement this)
        company = await get_company_by_id(request.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Create or retrieve Stripe customer
        customer_id = company.get('stripe_customer_id')
        if not customer_id:
            customer = stripe.Customer.create(
                email=company.get('billing_email') or company.get('owner_email'),
                name=company.get('name'),
                metadata={'company_id': request.company_id}
            )
            customer_id = customer.id
            
            # Save customer ID to database
            await update_company_stripe_customer(request.company_id, customer_id)

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url or f"https://pulsebridge.ai/dashboard/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url or "https://pulsebridge.ai/pricing",
            metadata={
                'company_id': request.company_id
            },
            trial_period_days=15,  # 15-day trial
            allow_promotion_codes=True
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Checkout session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@router.post("/create-portal-session")
async def create_portal_session(request: CreatePortalRequest):
    """
    Create Stripe customer portal session for subscription management
    """
    try:
        # Get company with Stripe customer ID
        company = await get_company_by_id(request.company_id)
        if not company or not company.get('stripe_customer_id'):
            raise HTTPException(status_code=404, detail="No billing account found")

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=company['stripe_customer_id'],
            return_url=request.return_url or "https://pulsebridge.ai/dashboard/billing"
        )

        return {
            "portal_url": portal_session.url
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Portal error: {str(e)}")
    except Exception as e:
        logger.error(f"Portal session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

@router.get("/subscription-status/{company_id}")
async def get_subscription_status(company_id: str) -> SubscriptionStatusResponse:
    """
    Get current subscription status for company
    """
    try:
        company = await get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Default response for companies without Stripe
        if not company.get('stripe_customer_id'):
            return SubscriptionStatusResponse(
                subscription_id=None,
                status="trial",
                subscription_tier=company.get('subscription_tier', 'trial'),
                trial_end=company.get('trial_ends_at'),
                customer_id=None
            )

        # Get latest subscription from Stripe
        subscriptions = stripe.Subscription.list(
            customer=company['stripe_customer_id'],
            status='all',
            limit=1
        )

        if subscriptions.data:
            sub = subscriptions.data[0]
            
            # Map Stripe price ID to subscription tier
            tier = get_tier_from_price_id(sub.items.data[0].price.id)
            
            return SubscriptionStatusResponse(
                subscription_id=sub.id,
                status=sub.status,
                current_period_end=datetime.fromtimestamp(sub.current_period_end),
                subscription_tier=tier,
                trial_end=datetime.fromtimestamp(sub.trial_end) if sub.trial_end else None,
                customer_id=company['stripe_customer_id']
            )
        else:
            return SubscriptionStatusResponse(
                subscription_id=None,
                status="no_subscription",
                subscription_tier=company.get('subscription_tier', 'trial'),
                trial_end=company.get('trial_ends_at'),
                customer_id=company['stripe_customer_id']
            )

    except Exception as e:
        logger.error(f"Subscription status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Stripe webhooks for subscription events
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        background_tasks.add_task(handle_checkout_completed, event['data']['object'])
    elif event['type'] == 'customer.subscription.created':
        background_tasks.add_task(handle_subscription_created, event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        background_tasks.add_task(handle_subscription_updated, event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        background_tasks.add_task(handle_subscription_cancelled, event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        background_tasks.add_task(handle_payment_succeeded, event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        background_tasks.add_task(handle_payment_failed, event['data']['object'])

    return {"received": True}

# Helper functions (implement these based on your database structure)
from app.billing_database import (
    get_company_by_id,
    update_company_stripe_customer,
    update_company_subscription,
    get_company_by_stripe_customer,
    log_billing_event
)

def get_tier_from_price_id(price_id: str) -> str:
    """Map Stripe price ID to subscription tier"""
    for tier, stripe_price_id in PRICE_IDS.items():
        if stripe_price_id == price_id:
            return tier
    return 'trial'

# Webhook handlers

async def handle_checkout_completed(session):
    """Handle successful checkout"""
    company_id = session.metadata.get('company_id')
    if company_id:
        logger.info(f"Checkout completed for company {company_id}")
        await log_billing_event(company_id, 'checkout_completed', {
            'session_id': session.id,
            'amount': session.amount_total
        })

async def handle_subscription_created(subscription):
    """Handle new subscription creation"""
    customer_id = subscription.customer
    tier = get_tier_from_price_id(subscription.items.data[0].price.id)
    
    # Get company by customer ID
    company = await get_company_by_stripe_customer(customer_id)
    if company:
        # Update company subscription
        await update_company_subscription(company['id'], {
            'subscription_tier': tier,
            'subscription_id': subscription.id,
            'status': subscription.status,
            'trial_end': subscription.trial_end,
            'current_period_end': subscription.current_period_end
        })
        
        await log_billing_event(company['id'], 'subscription_created', {
            'subscription_id': subscription.id,
            'tier': tier
        })
    
    logger.info(f"Subscription created for customer {customer_id}, tier: {tier}")

async def handle_subscription_updated(subscription):
    """Handle subscription changes (upgrades, downgrades)"""
    customer_id = subscription.customer
    tier = get_tier_from_price_id(subscription.items.data[0].price.id)
    
    company = await get_company_by_stripe_customer(customer_id)
    if company:
        await update_company_subscription(company['id'], {
            'subscription_tier': tier,
            'status': subscription.status,
            'current_period_end': subscription.current_period_end
        })
        
        await log_billing_event(company['id'], 'subscription_updated', {
            'subscription_id': subscription.id,
            'new_tier': tier
        })
    
    logger.info(f"Subscription updated for customer {customer_id}, new tier: {tier}")

async def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.customer
    
    company = await get_company_by_stripe_customer(customer_id)
    if company:
        await update_company_subscription(company['id'], {
            'status': 'cancelled',
            'account_status': 'cancelled'
        })
        
        await log_billing_event(company['id'], 'subscription_cancelled', {
            'subscription_id': subscription.id
        })
    
    logger.info(f"Subscription cancelled for customer {customer_id}")

async def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.customer
    
    company = await get_company_by_stripe_customer(customer_id)
    if company:
        await log_billing_event(company['id'], 'payment_succeeded', {
            'invoice_id': invoice.id,
            'amount': invoice.amount_paid
        })
    
    logger.info(f"Payment succeeded for customer {customer_id}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice.customer
    
    company = await get_company_by_stripe_customer(customer_id)
    if company:
        await log_billing_event(company['id'], 'payment_failed', {
            'invoice_id': invoice.id,
            'amount': invoice.amount_due
        })
    
    logger.info(f"Payment failed for customer {customer_id}")