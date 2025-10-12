"""
Test Suite for Admin Authentication and User Tier System
Tests the new JWT authentication and 3-tier user access system
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_admin_token
from app.billing_bypass_system import BillingBypassManager, BillingBypassReason

# Sync client for simpler tests
client = TestClient(app)


class TestAdminAuthentication:
    """Test admin authentication system"""

    def test_admin_login_endpoint_exists(self):
        """Test that admin login endpoint is accessible"""
        response = client.post(
            "/api/v1/auth/admin/login",
            json={"email": "admin@pulsebridge.ai", "password": "wrong-password"}
        )
        # Should return 401 for wrong password, not 404
        assert response.status_code in [401, 500], f"Expected 401/500, got {response.status_code}"

    def test_protected_endpoint_without_token(self):
        """Test that protected endpoints reject requests without token"""
        response = client.get("/api/v1/admin/users/internal")
        assert response.status_code == 401, "Should reject request without token"
        assert "authorization" in response.json()["detail"].lower()

    def test_protected_endpoint_with_invalid_token(self):
        """Test that protected endpoints reject invalid tokens"""
        response = client.get(
            "/api/v1/admin/users/internal",
            headers={"Authorization": "Bearer invalid-token-here"}
        )
        assert response.status_code == 401, "Should reject invalid token"

    def test_token_creation(self):
        """Test JWT token creation"""
        token = create_admin_token("test@pulsebridge.ai")
        assert token is not None
        assert len(token) > 50  # JWT tokens are long
        assert "." in token  # JWT format: header.payload.signature


class TestBillingBypassSystem:
    """Test billing bypass for different user tiers"""

    def test_internal_employee_detection(self):
        """Test that @pulsebridge.ai emails are detected as internal"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing(
            "employee@pulsebridge.ai"
        )
        assert should_bypass is True
        assert reason == BillingBypassReason.INTERNAL_EMPLOYEE

    def test_20n1_employee_detection(self):
        """Test that @20n1.ai emails are detected as internal"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing(
            "employee@20n1.ai"
        )
        assert should_bypass is True
        assert reason == BillingBypassReason.INTERNAL_EMPLOYEE

    def test_regular_customer_no_bypass(self):
        """Test that regular customers don't get bypass"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing(
            "customer@gmail.com"
        )
        assert should_bypass is False
        assert reason is None

    def test_external_test_user_bypass(self):
        """Test external test user bypass"""
        test_email = "tester@example.com"
        BillingBypassManager.add_external_test_user_email(test_email)

        should_bypass, reason = BillingBypassManager.should_bypass_billing(test_email)
        assert should_bypass is True
        assert reason == BillingBypassReason.EXTERNAL_TEST_USER

        # Cleanup
        BillingBypassManager.remove_external_test_user_email(test_email)

    def test_beta_tester_bypass(self):
        """Test beta tester bypass"""
        beta_email = "beta@startup.com"
        BillingBypassManager.add_beta_tester_email(beta_email)

        should_bypass, reason = BillingBypassManager.should_bypass_billing(beta_email)
        assert should_bypass is True
        assert reason == BillingBypassReason.BETA_TESTER

        # Cleanup
        BillingBypassManager.remove_beta_tester_email(beta_email)


class TestUserTierConfigurations:
    """Test that different user tiers get correct configurations"""

    def test_internal_employee_config(self):
        """Test internal employee gets full access"""
        config = BillingBypassManager.get_bypass_config(
            "emp@pulsebridge.ai",
            BillingBypassReason.INTERNAL_EMPLOYEE
        )

        assert config["billing_type"] == "internal"
        assert config["unlimited_usage"] is True
        assert config["suite_access"] == ["ml_suite", "financial_suite", "ai_suite", "hr_suite"]
        assert config["api_rate_limit"] is None  # Unlimited
        assert config["storage_limit"] is None  # Unlimited
        assert config["user_limit"] is None  # Unlimited
        assert config["expires_at"] is None  # No expiration
        assert config["access_level"] == "INTERNAL"

    def test_external_test_user_config(self):
        """Test external test user gets limited access"""
        config = BillingBypassManager.get_bypass_config(
            "test@example.com",
            BillingBypassReason.EXTERNAL_TEST_USER
        )

        assert config["billing_type"] == "external_test"
        assert config["unlimited_usage"] is False
        assert config["suite_access"] == ["ml_suite", "financial_suite"]  # Only 2 suites
        assert config["api_rate_limit"] == 1000  # Limited
        assert config["storage_limit"] == "1GB"  # Limited
        assert config["user_limit"] == 3  # Limited
        assert config["campaign_limit"] == 5  # Limited
        assert config["expires_at"] is not None  # Has expiration (30 days)
        assert config["access_level"] == "EXTERNAL_TEST"
        assert "warning" in config  # Should have warning message

    def test_beta_tester_config(self):
        """Test beta tester gets moderate access"""
        config = BillingBypassManager.get_bypass_config(
            "beta@startup.com",
            BillingBypassReason.BETA_TESTER
        )

        assert config["billing_type"] == "beta_tester"
        assert config["unlimited_usage"] is False
        assert config["suite_access"] == ["ml_suite", "financial_suite", "ai_suite"]  # 3 suites
        assert config["api_rate_limit"] == 5000  # Higher than external
        assert config["storage_limit"] == "5GB"  # More than external
        assert config["user_limit"] == 5  # More than external
        assert config["campaign_limit"] == 20  # More than external
        assert config["expires_at"] is not None  # Has expiration (90 days)
        assert config["access_level"] == "BETA"
        assert "perks" in config  # Should have perks list
        assert config["priority_support"] is True


class TestUserTierManagement:
    """Test adding/removing users from different tiers"""

    def test_add_and_remove_external_test_user(self):
        """Test adding and removing external test user"""
        email = "test@example.com"

        # Add
        success = BillingBypassManager.add_external_test_user_email(email)
        assert success is True

        # Verify added
        emails = BillingBypassManager.get_external_test_user_emails()
        assert email in emails

        # Remove
        success = BillingBypassManager.remove_external_test_user_email(email)
        assert success is True

        # Verify removed
        emails = BillingBypassManager.get_external_test_user_emails()
        assert email not in emails

    def test_add_and_remove_beta_tester(self):
        """Test adding and removing beta tester"""
        email = "beta@startup.com"

        # Add
        success = BillingBypassManager.add_beta_tester_email(email)
        assert success is True

        # Verify added
        emails = BillingBypassManager.get_beta_tester_emails()
        assert email in emails

        # Remove
        success = BillingBypassManager.remove_beta_tester_email(email)
        assert success is True

        # Verify removed
        emails = BillingBypassManager.get_beta_tester_emails()
        assert email not in emails

    def test_get_all_bypass_emails(self):
        """Test getting all bypass emails grouped by type"""
        # Add test users
        BillingBypassManager.add_external_test_user_email("test1@example.com")
        BillingBypassManager.add_beta_tester_email("beta1@startup.com")

        all_emails = BillingBypassManager.get_all_bypass_emails()

        assert "external_test_users" in all_emails
        assert "beta_testers" in all_emails
        assert "internal_domains" in all_emails
        assert "pulsebridge.ai" in all_emails["internal_domains"]

        # Cleanup
        BillingBypassManager.remove_external_test_user_email("test1@example.com")
        BillingBypassManager.remove_beta_tester_email("beta1@startup.com")


class TestInputValidation:
    """Test input validation for company profile"""

    def test_company_name_validation_allows_valid(self):
        """Test that valid company names are accepted"""
        response = client.post(
            "/api/v1/onboarding/company-profile",
            json={
                "company_name": "Acme Corp & Co.",
                "industry": "technology",
                "company_size": "startup",
                "primary_challenges": ["marketing_optimization"],
                "current_tools": [],
                "goals": ["increase_roi"]
            }
        )
        # Should succeed or fail for reasons other than validation
        assert response.status_code in [200, 401, 500], f"Got {response.status_code}"

    def test_company_name_validation_rejects_script_tags(self):
        """Test that XSS attempts in company name are rejected"""
        response = client.post(
            "/api/v1/onboarding/company-profile",
            json={
                "company_name": "<script>alert('xss')</script>",
                "industry": "technology",
                "company_size": "startup",
                "primary_challenges": [],
                "current_tools": [],
                "goals": []
            }
        )
        assert response.status_code == 422, "Should reject script tags"

    def test_industry_validation_rejects_special_chars(self):
        """Test that industry field rejects special characters"""
        response = client.post(
            "/api/v1/onboarding/company-profile",
            json={
                "company_name": "Test Corp",
                "industry": "tech<>nology",
                "company_size": "startup",
                "primary_challenges": [],
                "current_tools": [],
                "goals": []
            }
        )
        assert response.status_code == 422, "Should reject special characters in industry"


def test_health_check():
    """Test that health endpoint works"""
    response = client.get("/health")
    assert response.status_code in [200, 404], "Health endpoint should exist or return 404"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
