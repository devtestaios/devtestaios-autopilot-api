# Testing Strategy for Onboarding & Billing Bypass

## Test Coverage Analysis

### Current Test Coverage: ~0%
No test files found for new modules. Production deployment without tests is **HIGH RISK**.

---

## Unit Tests

### 1. Billing Bypass Manager Tests

**File:** `tests/test_billing_bypass_system.py`

```python
import pytest
from app.billing_bypass_system import BillingBypassManager, BillingBypassReason

class TestBillingBypassManager:
    """Test billing bypass detection logic"""

    def test_internal_domain_bypass(self):
        """Test that @pulsebridge.ai emails bypass billing"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing("john@pulsebridge.ai")

        assert should_bypass is True
        assert reason == BillingBypassReason.INTERNAL_EMPLOYEE

    def test_20n1_domain_bypass(self):
        """Test that @20n1.ai emails bypass billing"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing("sarah@20n1.ai")

        assert should_bypass is True
        assert reason == BillingBypassReason.INTERNAL_EMPLOYEE

    def test_regular_customer_no_bypass(self):
        """Test that regular customers don't bypass"""
        should_bypass, reason = BillingBypassManager.should_bypass_billing("customer@gmail.com")

        assert should_bypass is False
        assert reason is None

    def test_test_user_email_bypass(self):
        """Test that added test user emails bypass"""
        test_email = "tester@example.com"
        BillingBypassManager.add_test_user_email(test_email)

        should_bypass, reason = BillingBypassManager.should_bypass_billing(test_email)

        assert should_bypass is True
        assert reason == BillingBypassReason.TEST_USER

    def test_bypass_config_internal_employee(self):
        """Test internal employee gets unlimited access"""
        config = BillingBypassManager.get_bypass_config(
            "emp@pulsebridge.ai",
            BillingBypassReason.INTERNAL_EMPLOYEE
        )

        assert config["bypass_billing"] is True
        assert config["unlimited_usage"] is True
        assert config["api_rate_limit"] is None  # Unlimited
        assert config["expires_at"] is None  # No expiration
        assert "ml_suite" in config["suite_access"]

    def test_bypass_config_test_user(self):
        """Test test user gets limited but generous access"""
        config = BillingBypassManager.get_bypass_config(
            "test@example.com",
            BillingBypassReason.TEST_USER
        )

        assert config["bypass_billing"] is True
        assert config["unlimited_usage"] is True
        assert config["api_rate_limit"] == 10000  # High but limited
        assert config["expires_at"] is not None  # Has expiration

    def test_case_insensitive_email(self):
        """Test that email case doesn't matter"""
        should_bypass1, _ = BillingBypassManager.should_bypass_billing("JOHN@PULSEBRIDGE.AI")
        should_bypass2, _ = BillingBypassManager.should_bypass_billing("john@pulsebridge.ai")

        assert should_bypass1 == should_bypass2 == True

    def test_suite_access_validation(self):
        """Test suite access validation for bypass users"""
        allowed = BillingBypassManager.validate_suite_access(
            "emp@pulsebridge.ai",
            ["ml_suite", "financial_suite", "hr_suite"]
        )

        # Internal employees get all requested suites
        assert len(allowed) == 3
        assert "ml_suite" in allowed

    def test_usage_limit_check_internal(self):
        """Test internal users have no usage limits"""
        within_limits, limit = BillingBypassManager.check_usage_limits(
            "emp@pulsebridge.ai",
            "api_calls",
            current_usage=1000000  # High usage
        )

        assert within_limits is True
        assert limit is None  # Unlimited
```

**Run tests:**
```bash
pytest tests/test_billing_bypass_system.py -v
```

---

### 2. Pricing Engine Tests

**File:** `tests/test_modular_pricing_engine.py`

```python
import pytest
from decimal import Decimal
from app.modular_pricing_engine import (
    ModularPricingEngine,
    CompanySize,
    OnboardingProfile,
    Suite
)

class TestModularPricingEngine:
    """Test pricing calculations and recommendations"""

    @pytest.fixture
    def engine(self):
        return ModularPricingEngine()

    def test_single_suite_no_discount(self, engine):
        """Test single suite gets no bundle discount"""
        pricing = engine.calculate_pricing(
            ["predictive_analytics"],
            CompanySize.STARTUP
        )

        assert pricing.bundle_discount_percent == Decimal("0.0")
        assert pricing.company_size_multiplier == Decimal("1.0")

    def test_two_suites_10_percent_discount(self, engine):
        """Test 2 suites get 10% bundle discount"""
        pricing = engine.calculate_pricing(
            ["predictive_analytics", "financial_management"],
            CompanySize.STARTUP
        )

        assert pricing.bundle_discount_percent == Decimal("10.0")

    def test_three_suites_20_percent_discount(self, engine):
        """Test 3 suites get 20% bundle discount"""
        pricing = engine.calculate_pricing(
            ["predictive_analytics", "financial_management", "conversational_ai"],
            CompanySize.STARTUP
        )

        assert pricing.bundle_discount_percent == Decimal("20.0")

    def test_all_suites_30_percent_discount(self, engine):
        """Test all 4 suites get 30% bundle discount"""
        pricing = engine.calculate_pricing(
            ["predictive_analytics", "financial_management", "conversational_ai", "hr_management"],
            CompanySize.STARTUP
        )

        assert pricing.bundle_discount_percent == Decimal("30.0")

    def test_company_size_multipliers(self, engine):
        """Test company size affects pricing"""
        startup_pricing = engine.calculate_pricing(["predictive_analytics"], CompanySize.STARTUP)
        small_pricing = engine.calculate_pricing(["predictive_analytics"], CompanySize.SMALL_BUSINESS)
        medium_pricing = engine.calculate_pricing(["predictive_analytics"], CompanySize.MEDIUM_BUSINESS)

        # Prices should increase with company size
        assert startup_pricing.final_monthly_price < small_pricing.final_monthly_price
        assert small_pricing.final_monthly_price < medium_pricing.final_monthly_price

    def test_annual_billing_discount(self, engine):
        """Test annual billing gives ~17% discount (2 months free)"""
        monthly_pricing = engine.calculate_pricing(
            ["predictive_analytics"],
            CompanySize.STARTUP,
            annual_billing=False
        )

        annual_pricing = engine.calculate_pricing(
            ["predictive_analytics"],
            CompanySize.STARTUP,
            annual_billing=True
        )

        # Annual should be cheaper per month
        assert annual_pricing.final_monthly_price < monthly_pricing.final_monthly_price
        assert annual_pricing.annual_discount_percent == Decimal("16.67")

    def test_smart_recommendations(self, engine):
        """Test AI-driven suite recommendations"""
        profile = OnboardingProfile(
            company_name="Test Marketing Agency",
            industry="marketing_agency",
            company_size=CompanySize.STARTUP,
            employees_count=5,
            primary_challenges=["marketing_optimization", "financial_management"],
            current_tools=["HubSpot", "QuickBooks"],
            goals=["increase_roi", "automate_billing"],
            estimated_monthly_spend=Decimal("5000")
        )

        recommendations = engine.get_smart_recommendations(profile)

        # Marketing agency should get predictive analytics and financial suite
        assert "predictive_analytics" in recommendations
        assert "financial_management" in recommendations

    def test_roi_analysis(self, engine):
        """Test ROI calculation accuracy"""
        roi = engine.get_roi_analysis(
            ["predictive_analytics", "financial_management"],
            CompanySize.STARTUP
        )

        assert roi["monthly_investment"] > 0
        assert roi["monthly_savings"] > roi["monthly_investment"]  # Should show positive ROI
        assert roi["roi_percentage"] > 0
        assert "savings_breakdown" in roi

    def test_competitor_comparison(self, engine):
        """Test competitor pricing comparison"""
        comparison = engine.get_competitor_comparison(
            ["predictive_analytics", "conversational_ai"]
        )

        assert comparison["competitor_total_cost"] > comparison["our_cost"]
        assert comparison["savings_percentage"] > 0
        assert len(comparison["tools_replaced"]) == 2

    def test_decimal_precision(self, engine):
        """Test that pricing uses proper decimal precision"""
        pricing = engine.calculate_pricing(
            ["predictive_analytics"],
            CompanySize.STARTUP
        )

        # All prices should be exact to 2 decimal places
        assert str(pricing.final_monthly_price).count('.') == 1
        assert len(str(pricing.final_monthly_price).split('.')[-1]) <= 2

    def test_invalid_suite_handling(self, engine):
        """Test handling of invalid suite names"""
        pricing = engine.calculate_pricing(
            ["invalid_suite", "predictive_analytics"],
            CompanySize.STARTUP
        )

        # Should ignore invalid suite and continue
        assert len(pricing.selected_suites) == 2  # Both kept in list
        assert len(pricing.suite_costs) == 1  # But only valid one priced
```

**Run tests:**
```bash
pytest tests/test_modular_pricing_engine.py -v
```

---

## Integration Tests

### 3. Onboarding Flow Integration Tests

**File:** `tests/integration/test_onboarding_flow.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
class TestOnboardingIntegration:
    """Test complete onboarding flow"""

    async def test_internal_user_full_flow(self):
        """Test internal user completes onboarding without payment"""
        async with AsyncClient(app=app, base_url="http://test") as client:

            # Step 1: Create company profile as internal user
            response = await client.post("/api/v1/onboarding/company-profile", json={
                "company_name": "PulseBridge Internal Test",
                "industry": "technology",
                "company_size": "startup",
                "employees_count": 5,
                "primary_challenges": ["marketing_optimization"],
                "current_tools": [],
                "goals": ["increase_roi"],
                "user_email": "test@pulsebridge.ai"  # Internal email
            })

            assert response.status_code == 200
            data = response.json()

            # Verify demo mode activated
            assert data["demo_mode_info"] is not None
            assert data["demo_mode_info"]["demo_mode"] is True
            assert data["demo_mode_info"]["full_access"] is True

            session_id = data["session_id"]

            # Step 2: Calculate pricing (should show bypass)
            response = await client.post("/api/v1/onboarding/calculate-pricing", json={
                "selected_suites": ["predictive_analytics", "financial_management"],
                "company_size": "startup",
                "annual_billing": False,
                "user_email": "test@pulsebridge.ai"
            })

            assert response.status_code == 200
            data = response.json()

            # Verify billing bypass active
            assert data["billing_bypass"] is not None
            assert data["billing_bypass"]["bypass_active"] is True
            assert data["billing_bypass"]["reason"] == "internal_employee"

            # Step 3: Complete demo experience
            response = await client.post("/api/v1/onboarding/complete-demo-experience", json={
                "session_id": session_id,
                "user_email": "test@pulsebridge.ai",
                "selected_configuration": {
                    "selected_suites": ["predictive_analytics", "financial_management"],
                    "custom_settings": {}
                }
            })

            assert response.status_code == 200
            data = response.json()

            # Verify platform access granted
            assert data["success"] is True
            assert data["authorization_status"]["billing_bypass_active"] is True
            assert data["authorization_status"]["access_level"] == "unlimited"

    async def test_regular_customer_requires_payment(self):
        """Test regular customer sees payment requirement"""
        async with AsyncClient(app=app, base_url="http://test") as client:

            response = await client.post("/api/v1/onboarding/calculate-pricing", json={
                "selected_suites": ["predictive_analytics"],
                "company_size": "startup",
                "annual_billing": False,
                "user_email": "customer@example.com"  # External email
            })

            assert response.status_code == 200
            data = response.json()

            # Verify no billing bypass
            assert data.get("billing_bypass") is None or data["billing_bypass"] is False

    async def test_suite_catalog_endpoint(self):
        """Test suite catalog returns all suites"""
        async with AsyncClient(app=app, base_url="http://test") as client:

            response = await client.get("/api/v1/onboarding/suite-catalog")

            assert response.status_code == 200
            data = response.json()

            assert "suites" in data
            assert len(data["suites"]) == 4  # 4 suites available
            assert "predictive_analytics" in data["suites"]
```

**Run integration tests:**
```bash
pytest tests/integration/test_onboarding_flow.py -v
```

---

## End-to-End Tests

### 4. E2E User Journey Tests

**File:** `tests/e2e/test_user_journeys.py`

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
class TestUserJourneys:
    """Test complete user journeys through frontend"""

    @pytest.mark.asyncio
    async def test_internal_employee_onboarding_journey(self):
        """Test internal employee onboarding from start to dashboard"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate to signup
            await page.goto("https://pulsebridge.ai/signup")

            # Fill in internal email
            await page.fill('input[name="email"]', 'test@pulsebridge.ai')
            await page.fill('input[name="company_name"]', 'Test Company')
            await page.click('button[type="submit"]')

            # Should see demo mode indicator
            demo_badge = await page.wait_for_selector('text=Demo Mode Active')
            assert demo_badge is not None

            # Complete company profile
            await page.select_option('select[name="company_size"]', 'startup')
            await page.click('button:text("Continue")')

            # Should skip payment page
            await page.wait_for_url('**/dashboard', timeout=5000)

            # Verify dashboard access
            assert '/dashboard' in page.url

            await browser.close()
```

---

## Test Data Fixtures

### 5. Reusable Test Data

**File:** `tests/conftest.py`

```python
import pytest
from app.billing_bypass_system import BillingBypassManager

@pytest.fixture
def internal_user_email():
    """Internal employee email"""
    return "employee@pulsebridge.ai"

@pytest.fixture
def test_user_email():
    """Test user email"""
    email = "test_user@example.com"
    BillingBypassManager.add_test_user_email(email)
    yield email
    BillingBypassManager.remove_test_user_email(email)

@pytest.fixture
def regular_customer_email():
    """Regular paying customer email"""
    return "customer@company.com"

@pytest.fixture
def sample_company_profile():
    """Sample company profile for testing"""
    return {
        "company_name": "Test Corp",
        "industry": "technology",
        "company_size": "startup",
        "employees_count": 10,
        "primary_challenges": ["marketing_optimization", "financial_management"],
        "current_tools": ["HubSpot", "QuickBooks"],
        "goals": ["increase_roi", "automate_processes"],
        "estimated_monthly_spend": 5000
    }

@pytest.fixture
def suite_selection():
    """Sample suite selection"""
    return ["predictive_analytics", "financial_management"]
```

---

## Test Coverage Goals

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `billing_bypass_system.py` | 95% | CRITICAL |
| `modular_pricing_engine.py` | 90% | HIGH |
| `business_setup_wizard.py` | 85% | HIGH |
| `admin_user_management.py` | 80% | MEDIUM |
| `billing_endpoints.py` | 85% | MEDIUM |

---

## CI/CD Integration

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov httpx

    - name: Run unit tests
      run: |
        pytest tests/ -v --cov=app --cov-report=term-missing

    - name: Check coverage threshold
      run: |
        pytest tests/ --cov=app --cov-fail-under=80

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

---

## Manual Testing Checklist

### Internal User Flow
- [ ] Create internal user via admin panel
- [ ] User receives onboarding email
- [ ] User starts onboarding wizard
- [ ] Demo mode badge shows on UI
- [ ] All suites recommended
- [ ] Pricing shown but marked "FREE for internal users"
- [ ] No payment step shown
- [ ] Dashboard access granted immediately
- [ ] All 4 suites accessible
- [ ] No usage limits enforced

### Test User Flow
- [ ] Add test user email via admin endpoint
- [ ] Test user starts onboarding
- [ ] Bypass active with expiration notice
- [ ] Limited usage quotas displayed
- [ ] Platform access granted

### Regular Customer Flow
- [ ] Customer starts onboarding normally
- [ ] No demo mode activated
- [ ] Payment step required
- [ ] Stripe checkout session created
- [ ] Access only after payment

### Edge Cases
- [ ] Session expires after 24 hours
- [ ] Invalid suite name handled gracefully
- [ ] Negative employee count rejected
- [ ] XSS attempt in company_name blocked
- [ ] Very long company_name truncated
- [ ] Concurrent session creation works
- [ ] Server restart doesn't lose in-progress sessions (after Redis)

---

## Test Execution

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/test_*.py -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/test_billing_bypass_system.py::TestBillingBypassManager::test_internal_domain_bypass -v

# Run and show print statements
pytest -v -s

# Run tests matching pattern
pytest -k "bypass" -v
```

---

## Next Steps

1. **THIS WEEK:** Write unit tests for billing bypass (CRITICAL)
2. **THIS WEEK:** Write pricing engine tests (HIGH)
3. **NEXT WEEK:** Integration tests for onboarding flow
4. **NEXT WEEK:** Set up CI/CD pipeline with automated tests
5. **ONGOING:** Maintain >80% test coverage for new code
