"""
Billing Bypass System for Internal Users
Automatically handles billing bypass for employees, test users, and internal accounts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BillingBypassReason(str, Enum):
    INTERNAL_EMPLOYEE = "internal_employee"
    TEST_USER = "test_user"
    BETA_TESTER = "beta_tester"
    PARTNER_ACCOUNT = "partner_account"
    CONTRACTOR = "contractor"
    DEVELOPER_ACCOUNT = "developer_account"
    ADMIN_OVERRIDE = "admin_override"

class BillingBypassManager:
    """Manages billing bypass logic for internal and test users"""
    
    # Email domains that automatically get internal status
    INTERNAL_DOMAINS = [
        "pulsebridge.ai",
        "20n1.ai",
        "20n1digital.com"
    ]
    
    # Specific test user emails (can be managed via admin dashboard)
    TEST_USER_EMAILS = set()
    
    # Partner domains that get special access
    PARTNER_DOMAINS = [
        # Add partner domains here
    ]
    
    @classmethod
    def should_bypass_billing(cls, email: str, user_data: Dict[str, Any] = None) -> tuple[bool, Optional[BillingBypassReason]]:
        """
        Determine if user should bypass billing based on email and user data
        Returns (should_bypass, reason)
        """
        email_lower = email.lower()
        
        # Check internal domains
        for domain in cls.INTERNAL_DOMAINS:
            if email_lower.endswith(f"@{domain}"):
                return True, BillingBypassReason.INTERNAL_EMPLOYEE
        
        # Check specific test user emails
        if email_lower in cls.TEST_USER_EMAILS:
            return True, BillingBypassReason.TEST_USER
        
        # Check partner domains
        for domain in cls.PARTNER_DOMAINS:
            if email_lower.endswith(f"@{domain}"):
                return True, BillingBypassReason.PARTNER_ACCOUNT
        
        # Check user data flags
        if user_data:
            if user_data.get("account_type") in ["internal_employee", "test_user", "beta_tester"]:
                return True, BillingBypassReason(user_data["account_type"])
            
            if user_data.get("bypass_billing", False):
                return True, BillingBypassReason.ADMIN_OVERRIDE
        
        return False, None
    
    @classmethod
    def get_bypass_config(cls, email: str, reason: BillingBypassReason) -> Dict[str, Any]:
        """Get billing bypass configuration for user"""
        base_config = {
            "bypass_billing": True,
            "payment_required": False,
            "trial_bypass": True,
            "unlimited_usage": True,
            "billing_type": "internal",
            "created_at": datetime.now(timezone.utc),
            "reason": reason.value
        }
        
        if reason == BillingBypassReason.INTERNAL_EMPLOYEE:
            base_config.update({
                "suite_access": ["ml_suite", "financial_suite", "ai_suite", "hr_suite"],
                "api_rate_limit": None,  # Unlimited
                "storage_limit": None,   # Unlimited
                "user_limit": None,      # Unlimited team members
                "expires_at": None       # No expiration
            })
        
        elif reason in [BillingBypassReason.TEST_USER, BillingBypassReason.BETA_TESTER]:
            base_config.update({
                "suite_access": ["ml_suite", "financial_suite", "ai_suite", "hr_suite"],
                "api_rate_limit": 10000,  # High but limited
                "storage_limit": "10GB",  # Generous for testing
                "user_limit": 10,         # Multiple team members for testing
                "expires_at": datetime.now(timezone.utc).replace(year=2026)  # 1 year
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
    def add_test_user_email(cls, email: str) -> bool:
        """Add email to test user list"""
        try:
            cls.TEST_USER_EMAILS.add(email.lower())
            logger.info(f"Added test user email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error adding test user email: {str(e)}")
            return False
    
    @classmethod
    def remove_test_user_email(cls, email: str) -> bool:
        """Remove email from test user list"""
        try:
            cls.TEST_USER_EMAILS.discard(email.lower())
            logger.info(f"Removed test user email: {email}")
            return True
        except Exception as e:
            logger.error(f"Error removing test user email: {str(e)}")
            return False
    
    @classmethod
    def get_test_user_emails(cls) -> List[str]:
        """Get list of all test user emails"""
        return list(cls.TEST_USER_EMAILS)
    
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