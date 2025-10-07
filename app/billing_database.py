"""
Database helper functions for Stripe billing integration
Connects billing system to existing Supabase database
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Supabase Integration (reuse from main.py)
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_AVAILABLE = True
    else:
        supabase = None
        SUPABASE_AVAILABLE = False
except ImportError:
    supabase = None
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

async def get_company_by_id(company_id: str) -> Optional[Dict[str, Any]]:
    """Get company from database"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available for company lookup")
        return None
    
    try:
        result = supabase.table('companies').select('*').eq('id', company_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching company {company_id}: {str(e)}")
        return None

async def update_company_stripe_customer(company_id: str, customer_id: str):
    """Save Stripe customer ID to company record"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available for stripe customer update")
        return
    
    try:
        supabase.table('companies').update({
            'stripe_customer_id': customer_id,
            'updated_at': datetime.now().isoformat()
        }).eq('id', company_id).execute()
        
        logger.info(f"Updated company {company_id} with Stripe customer {customer_id}")
    except Exception as e:
        logger.error(f"Error updating stripe customer for company {company_id}: {str(e)}")

async def update_company_subscription(company_id: str, subscription_data: Dict[str, Any]):
    """Update company subscription details"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available for subscription update")
        return
    
    try:
        # Prepare update data
        update_data = {
            'updated_at': datetime.now().isoformat()
        }
        
        # Map subscription data to database fields
        if 'subscription_tier' in subscription_data:
            update_data['subscription_tier'] = subscription_data['subscription_tier']
        
        if 'subscription_id' in subscription_data:
            update_data['stripe_subscription_id'] = subscription_data['subscription_id']
        
        if 'status' in subscription_data:
            # Map Stripe statuses to our account statuses
            stripe_status = subscription_data['status']
            if stripe_status in ['active', 'trialing']:
                update_data['account_status'] = 'active'
            elif stripe_status in ['canceled', 'unpaid']:
                update_data['account_status'] = 'cancelled'
            elif stripe_status == 'past_due':
                update_data['account_status'] = 'suspended'
        
        if 'trial_end' in subscription_data and subscription_data['trial_end']:
            update_data['trial_ends_at'] = subscription_data['trial_end'].isoformat()
        
        if 'current_period_end' in subscription_data and subscription_data['current_period_end']:
            update_data['subscription_ends_at'] = subscription_data['current_period_end'].isoformat()
        
        # Update database
        supabase.table('companies').update(update_data).eq('id', company_id).execute()
        
        logger.info(f"Updated subscription for company {company_id}: {update_data}")
    except Exception as e:
        logger.error(f"Error updating subscription for company {company_id}: {str(e)}")

async def get_company_by_stripe_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get company by Stripe customer ID"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        result = supabase.table('companies').select('*').eq('stripe_customer_id', customer_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching company by customer {customer_id}: {str(e)}")
        return None

async def log_billing_event(company_id: str, event_type: str, event_data: Dict[str, Any]):
    """Log billing events for audit trail"""
    if not SUPABASE_AVAILABLE:
        return
    
    try:
        supabase.table('audit_logs').insert({
            'company_id': company_id,
            'action': f'BILLING_{event_type.upper()}',
            'resource_type': 'subscription',
            'resource_id': event_data.get('subscription_id'),
            'new_values': event_data,
            'severity': 'info',
            'category': 'billing',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        logger.info(f"Logged billing event {event_type} for company {company_id}")
    except Exception as e:
        logger.error(f"Error logging billing event: {str(e)}")

# Usage limit helpers

async def check_usage_limits(company_id: str) -> Dict[str, Any]:
    """Check current usage against subscription limits"""
    if not SUPABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        # Get company subscription info
        company = await get_company_by_id(company_id)
        if not company:
            return {"error": "Company not found"}
        
        subscription_tier = company.get('subscription_tier', 'trial')
        
        # Define limits based on subscription tier (matches enterpriseAPI.ts)
        TIER_LIMITS = {
            'trial': {
                'users': 10,
                'storage_gb': 5,
                'api_calls_month': 5000,
                'campaigns': 10
            },
            'solo_professional': {
                'users': 1,
                'storage_gb': 10,
                'api_calls_month': 15000,
                'campaigns': 25
            },
            'growth_team': {
                'users': 3,
                'storage_gb': 25,
                'api_calls_month': 50000,
                'campaigns': 50
            },
            'professional_agency': {
                'users': 10,
                'storage_gb': 100,
                'api_calls_month': 150000,
                'campaigns': 200
            },
            'enterprise': {
                'users': 25,
                'storage_gb': 500,
                'api_calls_month': 500000,
                'campaigns': 1000
            },
            'enterprise_plus': {
                'users': -1,  # Unlimited
                'storage_gb': -1,
                'api_calls_month': -1,
                'campaigns': -1
            }
        }
        
        limits = TIER_LIMITS.get(subscription_tier, TIER_LIMITS['trial'])
        
        # Get current usage (you'll need to implement these queries based on your data)
        current_usage = {
            'users': company.get('current_user_count', 0),
            'storage_gb': company.get('current_storage_gb', 0),
            'api_calls_month': 0,  # TODO: Implement API call tracking
            'campaigns': 0  # TODO: Count active campaigns
        }
        
        # Calculate usage percentages
        usage_status = {}
        for metric, limit in limits.items():
            current = current_usage.get(metric, 0)
            if limit == -1:  # Unlimited
                usage_status[metric] = {
                    'current': current,
                    'limit': 'unlimited',
                    'percentage': 0,
                    'warning': False
                }
            else:
                percentage = (current / limit * 100) if limit > 0 else 0
                usage_status[metric] = {
                    'current': current,
                    'limit': limit,
                    'percentage': percentage,
                    'warning': percentage > 80  # Warning at 80% usage
                }
        
        return {
            'subscription_tier': subscription_tier,
            'usage': usage_status,
            'trial_ends_at': company.get('trial_ends_at'),
            'account_status': company.get('account_status', 'active')
        }
        
    except Exception as e:
        logger.error(f"Error checking usage limits: {str(e)}")
        return {"error": "Failed to check usage limits"}