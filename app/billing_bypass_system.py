"""
Billing Bypass System for Internal Users
Automatically handles billing bypass for employees, test users, and internal accounts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BillingBypassReason(str, Enum):
    # PulseBridge Internal (Full Access, No Expiration)
    INTERNAL_EMPLOYEE = "internal_employee"
    CONTRACTOR = "contractor"
    DEVELOPER_ACCOUNT = "developer_account"

    # External Test Users (Limited Access, Has Expiration)
    EXTERNAL_TEST_USER = "external_test_user"
    BETA_TESTER = "beta_tester"
    PARTNER_ACCOUNT = "partner_account"

    # Special Cases
    ADMIN_OVERRIDE = "admin_override"

class BillingBypassManager:
    """Manages billing bypass logic for internal and test users"""
    
    # PulseBridge internal domains - FULL ACCESS, NO LIMITS
    INTERNAL_DOMAINS = [
        "pulsebridge.ai",
        "20n1.ai",
        "20n1digital.com"
    ]

    # External test user emails (third-party testers) - LIMITED ACCESS
    EXTERNAL_TEST_USER_EMAILS = set()

    # Beta tester emails (early access customers) - MODERATE ACCESS
    BETA_TESTER_EMAILS = set()

    # Partner domains (business partners) - SPECIAL ACCESS
    PARTNER_DOMAINS = [
        # Add partner domains here
    ]
    
    @classmethod
    def should_bypass_billing(cls, email: str, user_data: Dict[str, Any] = None) -> tuple[bool, Optional[BillingBypassReason]]:
        """
        Determine if user should bypass billing based on email and user data
        Returns (should_bypass, reason)

        Priority Order:
        1. PulseBridge Internal Domains (HIGHEST ACCESS)
        2. External Test User Emails (LIMITED ACCESS)
        3. Beta Tester Emails (MODERATE ACCESS)
        4. Partner Domains (SPECIAL ACCESS)
        5. User Data Flags (VARIABLE ACCESS)
        """
        email_lower = email.lower()

        # PRIORITY 1: PulseBridge Internal Domains (Full Access, No Limits)
        for domain in cls.INTERNAL_DOMAINS:
            if email_lower.endswith(f"@{domain}"):
                logger.info(f"Internal employee detected: {email}")
                return True, BillingBypassReason.INTERNAL_EMPLOYEE

        # PRIORITY 2: External Test User Emails (Limited Access, Expires)
        if email_lower in cls.EXTERNAL_TEST_USER_EMAILS:
            logger.info(f"External test user detected: {email}")
            return True, BillingBypassReason.EXTERNAL_TEST_USER

        # PRIORITY 3: Beta Tester Emails (Moderate Access, Expires)
        if email_lower in cls.BETA_TESTER_EMAILS:
            logger.info(f"Beta tester detected: {email}")
            return True, BillingBypassReason.BETA_TESTER

        # PRIORITY 4: Partner Domains (Special Access)
        for domain in cls.PARTNER_DOMAINS:
            if email_lower.endswith(f"@{domain}"):
                logger.info(f"Partner account detected: {email}")
                return True, BillingBypassReason.PARTNER_ACCOUNT

        # PRIORITY 5: User Data Flags (Check account_type from database)
        if user_data:
            account_type = user_data.get("account_type")

            if account_type == "internal_employee":
                return True, BillingBypassReason.INTERNAL_EMPLOYEE
            elif account_type == "contractor":
                return True, BillingBypassReason.CONTRACTOR
            elif account_type == "developer_account":
                return True, BillingBypassReason.DEVELOPER_ACCOUNT
            elif account_type == "external_test_user":
                return True, BillingBypassReason.EXTERNAL_TEST_USER
            elif account_type == "beta_tester":
                return True, BillingBypassReason.BETA_TESTER

            # Admin override flag
            if user_data.get("bypass_billing", False):
                return True, BillingBypassReason.ADMIN_OVERRIDE

        return False, None
    
    @classmethod
    def get_bypass_config(cls, email: str, reason: BillingBypassReason) -> Dict[str, Any]:
        """
        Get billing bypass configuration for user

        Access Levels:
        - INTERNAL: Full access, no limits, no expiration
        - EXTERNAL_TEST: Limited access, expires in 30 days
        - BETA: Moderate access, expires in 90 days
        - PARTNER: Custom access based on partnership
        """
        base_config = {
            "bypass_billing": True,
            "payment_required": False,
            "trial_bypass": True,
            "created_at": datetime.now(timezone.utc),
            "reason": reason.value
        }

        # ===================================================================
        # TIER 1: PULSEBRIDGE INTERNAL (Full Access, No Limits, No Expiration)
        # ===================================================================
        if reason in [BillingBypassReason.INTERNAL_EMPLOYEE, BillingBypassReason.CONTRACTOR, BillingBypassReason.DEVELOPER_ACCOUNT]:
            base_config.update({
                "billing_type": "internal",
                "unlimited_usage": True,
                "suite_access": ["ml_suite", "financial_suite", "ai_suite", "hr_suite"],
                "api_rate_limit": None,  # Unlimited
                "storage_limit": None,   # Unlimited
                "user_limit": None,      # Unlimited team members
                "campaign_limit": None,  # Unlimited campaigns
                "expires_at": None,      # No expiration
                "priority_support": True,
                "white_glove_onboarding": True,
                "advanced_analytics": True,
                "custom_integrations": True,
                "access_level": "INTERNAL",
                "description": "PulseBridge Internal User - Full Platform Access"
            })

        # ===================================================================
        # TIER 2: EXTERNAL TEST USERS (Limited Access, 30 Day Expiration)
        # ===================================================================
        elif reason == BillingBypassReason.EXTERNAL_TEST_USER:
            base_config.update({
                "billing_type": "external_test",
                "unlimited_usage": False,
                "suite_access": ["ml_suite", "financial_suite"],  # Limited to 2 suites
                "api_rate_limit": 1000,   # 1,000 API calls/month
                "storage_limit": "1GB",   # 1GB storage
                "user_limit": 3,          # Max 3 team members
                "campaign_limit": 5,      # Max 5 campaigns
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30),  # 30 days
                "priority_support": False,
                "white_glove_onboarding": False,
                "advanced_analytics": False,
                "custom_integrations": False,
                "access_level": "EXTERNAL_TEST",
                "description": "External Test User - Limited 30-Day Trial",
                "warning": "⚠️ Trial expires in 30 days. Contact sales for extended access."
            })

        # ===================================================================
        # TIER 3: BETA TESTERS (Moderate Access, 90 Day Expiration)
        # ===================================================================
        elif reason == BillingBypassReason.BETA_TESTER:
            base_config.update({
                "billing_type": "beta_tester",
                "unlimited_usage": False,
                "suite_access": ["ml_suite", "financial_suite", "ai_suite"],  # 3 suites
                "api_rate_limit": 5000,   # 5,000 API calls/month
                "storage_limit": "5GB",   # 5GB storage
                "user_limit": 5,          # Max 5 team members
                "campaign_limit": 20,     # Max 20 campaigns
                "expires_at": datetime.now(timezone.utc) + timedelta(days=90),  # 90 days
                "priority_support": True,
                "white_glove_onboarding": True,
                "advanced_analytics": True,
                "custom_integrations": False,
                "access_level": "BETA",
                "description": "Beta Tester - Extended Trial Access",
                "perks": ["Early access to new features", "Direct feedback channel", "Beta community access"]
            })
        
        elif reason == BillingBypassReason.PARTNER_ACCOUNT:
            base_config.update({
                "suite_access": ["ml_suite", "ai_suite"],  # Limited access
                "api_rate_limit": 5000,
                "storage_limit": "5GB",
                "user_limit": 5,
                "expires_at": datetime.now(timezone.utc).replace(year=2026)
            })
        
        return base_config
    
    @classmethod
    def add_external_test_user_email(cls, email: str) -> bool:
        """Add email to external test user list (30-day limited access)"""
        try:
            cls.EXTERNAL_TEST_USER_EMAILS.add(email.lower())
            logger.info(f"Added external test user email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error adding external test user email: {str(e)}")
            return False

    @classmethod
    def remove_external_test_user_email(cls, email: str) -> bool:
        """Remove email from external test user list"""
        try:
            cls.EXTERNAL_TEST_USER_EMAILS.discard(email.lower())
            logger.info(f"Removed external test user email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error removing external test user email: {str(e)}")
            return False

    @classmethod
    def add_beta_tester_email(cls, email: str) -> bool:
        """Add email to beta tester list (90-day moderate access)"""
        try:
            cls.BETA_TESTER_EMAILS.add(email.lower())
            logger.info(f"Added beta tester email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error adding beta tester email: {str(e)}")
            return False

    @classmethod
    def remove_beta_tester_email(cls, email: str) -> bool:
        """Remove email from beta tester list"""
        try:
            cls.BETA_TESTER_EMAILS.discard(email.lower())
            logger.info(f"Removed beta tester email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error removing beta tester email: {str(e)}")
            return False

    @classmethod
    def get_external_test_user_emails(cls) -> List[str]:
        """Get list of all external test user emails"""
        return list(cls.EXTERNAL_TEST_USER_EMAILS)

    @classmethod
    def get_beta_tester_emails(cls) -> List[str]:
        """Get list of all beta tester emails"""
        return list(cls.BETA_TESTER_EMAILS)

    @classmethod
    def get_all_bypass_emails(cls) -> Dict[str, List[str]]:
        """Get all bypass emails grouped by type"""
        return {
            "external_test_users": list(cls.EXTERNAL_TEST_USER_EMAILS),
            "beta_testers": list(cls.BETA_TESTER_EMAILS),
            "internal_domains": cls.INTERNAL_DOMAINS,
            "partner_domains": cls.PARTNER_DOMAINS
        }
    
    @classmethod
    def validate_suite_access(cls, user_email: str, requested_suites: List[str]) -> List[str]:
        """Validate and return allowed suite access for user"""
        should_bypass, reason = cls.should_bypass_billing(user_email)
        
        if not should_bypass:
            return []  # No bypass, normal billing applies
        
        bypass_config = cls.get_bypass_config(user_email, reason)
        allowed_suites = bypass_config.get("suite_access", [])
        
        # Return intersection of requested and allowed suites
        return [suite for suite in requested_suites if suite in allowed_suites]
    
    @classmethod
    def check_usage_limits(cls, user_email: str, usage_type: str, current_usage: int) -> tuple[bool, Optional[int]]:
        """
        Check if user exceeds usage limits
        Returns (within_limits, limit_value)
        """
        should_bypass, reason = cls.should_bypass_billing(user_email)
        
        if not should_bypass:
            return True, None  # Normal billing limits apply
        
        bypass_config = cls.get_bypass_config(user_email, reason)
        
        if usage_type == "api_calls":
            limit = bypass_config.get("api_rate_limit")
            if limit is None:
                return True, None  # Unlimited
            return current_usage <= limit, limit
        
        elif usage_type == "storage":
            limit = bypass_config.get("storage_limit")
            if limit is None:
                return True, None  # Unlimited
            # Convert limit string to bytes for comparison
            # This is simplified - would need proper conversion logic
            return True, limit
        
        elif usage_type == "users":
            limit = bypass_config.get("user_limit")
            if limit is None:
                return True, None  # Unlimited
            return current_usage <= limit, limit
        
        return True, None

def integrate_billing_bypass_middleware():
    """
    Middleware function to integrate billing bypass with existing billing endpoints
    This would be called before billing operations
    """
    def billing_bypass_middleware(func):
        def wrapper(*args, **kwargs):
            # Extract user email from request
            request = kwargs.get('request') or args[0] if args else None
            user_email = getattr(request, 'user_email', None)
            
            if user_email:
                should_bypass, reason = BillingBypassManager.should_bypass_billing(user_email)
                
                if should_bypass:
                    # User should bypass billing - return success without Stripe
                    bypass_config = BillingBypassManager.get_bypass_config(user_email, reason)
                    
                    return {
                        "success": True,
                        "billing_bypass": True,
                        "reason": reason.value,
                        "config": bypass_config,
                        "message": f"Billing bypassed for {reason.value}"
                    }
            
            # Normal billing flow
            return func(*args, **kwargs)
        
        return wrapper
    return billing_bypass_middleware

# Integration functions for existing billing system
def check_billing_bypass_before_payment(user_email: str, suite_selection: List[str]) -> Dict[str, Any]:
    """
    Check if user should bypass billing before creating Stripe session
    """
    should_bypass, reason = BillingBypassManager.should_bypass_billing(user_email)
    
    if should_bypass:
        bypass_config = BillingBypassManager.get_bypass_config(user_email, reason)
        allowed_suites = BillingBypassManager.validate_suite_access(user_email, suite_selection)
        
        return {
            "bypass_billing": True,
            "reason": reason.value,
            "allowed_suites": allowed_suites,
            "config": bypass_config,
            "skip_stripe": True
        }
    
    return {
        "bypass_billing": False,
        "skip_stripe": False
    }

def get_user_billing_status(user_email: str) -> Dict[str, Any]:
    """
    Get comprehensive billing status for user
    """
    should_bypass, reason = BillingBypassManager.should_bypass_billing(user_email)
    
    if should_bypass:
        bypass_config = BillingBypassManager.get_bypass_config(user_email, reason)
        
        return {
            "billing_type": "bypass",
            "reason": reason.value,
            "payment_required": False,
            "trial_status": "unlimited",
            "suite_access": bypass_config["suite_access"],
            "limits": {
                "api_calls": bypass_config.get("api_rate_limit"),
                "storage": bypass_config.get("storage_limit"),
                "users": bypass_config.get("user_limit")
            },
            "expires_at": bypass_config.get("expires_at")
        }
    
    return {
        "billing_type": "standard",
        "payment_required": True,
        "trial_status": "active" # Would check actual trial status
    }