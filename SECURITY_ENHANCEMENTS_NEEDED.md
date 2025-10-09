# Security Enhancements Required

## CRITICAL: Admin Endpoint Authentication

### Current Issue
All admin user management endpoints are **completely open** with no authentication:

```python
# app/admin_user_management.py:87-95
@router.post("/internal")
async def create_internal_user(request: CreateInternalUserRequest):
    # NO AUTH CHECK - Anyone can create internal users!
```

### Required Fix
Add authentication dependency to all admin endpoints:

```python
from fastapi import Depends
from app.auth import verify_admin_token  # You'll need to implement this

@router.post("/internal")
async def create_internal_user(
    request: CreateInternalUserRequest,
    admin_user: dict = Depends(verify_admin_token)  # Require admin auth
):
    # Only authenticated admins can create users
```

### Endpoints Needing Protection
1. `POST /api/v1/admin/users/internal` - Create internal user
2. `GET /api/v1/admin/users/internal` - List all users
3. `PUT /api/v1/admin/users/internal/{user_id}` - Update user
4. `DELETE /api/v1/admin/users/internal/{user_id}` - Delete user
5. `POST /api/v1/admin/users/bulk-operation` - Bulk operations
6. `POST /api/v1/admin/users/test-account` - Create test account
7. `POST /api/v1/billing/bypass/add-test-user` - Add to bypass list
8. `DELETE /api/v1/billing/bypass/remove-test-user` - Remove from bypass
9. `GET /api/v1/billing/bypass/test-users` - List bypass users

---

## HIGH: Input Sanitization

### XSS Prevention
Add regex validation to prevent malicious input:

```python
class CompanyProfileRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        regex=r"^[a-zA-Z0-9\s\-\.&',]+$"  # Alphanumeric, spaces, common business chars
    )

    industry: str = Field(
        ...,
        regex=r"^[a-zA-Z\s\-_]+$"  # Letters, spaces, hyphens
    )
```

### Email Validation
Use proper email validation library:

```python
from pydantic import EmailStr

class CreateInternalUserRequest(BaseModel):
    email: EmailStr  # Built-in email validation
```

---

## MEDIUM: Rate Limiting

Add rate limiting to prevent abuse of public endpoints:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/company-profile")
@limiter.limit("10/minute")  # Max 10 profiles per minute per IP
async def create_company_profile(...):
    pass
```

---

## MEDIUM: Persistent Test User Storage

Replace in-memory set with database storage:

```python
# Current (UNSAFE - lost on restart)
TEST_USER_EMAILS = set()

# Recommended
class BillingBypassManager:
    @classmethod
    async def add_test_user_email(cls, email: str) -> bool:
        try:
            # Save to database instead
            supabase.table('billing_bypass_users').insert({
                'email': email.lower(),
                'bypass_reason': 'test_user',
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding test user: {e}")
            return False

    @classmethod
    async def should_bypass_billing(cls, email: str) -> tuple[bool, Optional[BillingBypassReason]]:
        # Check database instead of in-memory set
        result = supabase.table('billing_bypass_users').select('*').eq('email', email.lower()).execute()
        if result.data:
            return True, BillingBypassReason.TEST_USER
        # ... rest of logic
```

---

## LOW: API Key Exposure Prevention

Ensure Stripe keys never logged or returned in responses:

```python
# Add to logging config
import logging

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Redact sensitive data from logs
        record.msg = re.sub(r'sk_live_\w+', 'sk_live_***REDACTED***', str(record.msg))
        return True

logger.addFilter(SensitiveDataFilter())
```

---

## Security Checklist

- [ ] Implement admin authentication middleware
- [ ] Add RBAC enforcement to all admin endpoints
- [ ] Validate and sanitize all user inputs (company_name, industry, etc.)
- [ ] Move TEST_USER_EMAILS to database
- [ ] Add rate limiting to public endpoints
- [ ] Implement CSRF protection for state-changing operations
- [ ] Add audit logging for all admin actions
- [ ] Ensure Stripe keys never appear in logs or responses
- [ ] Add request signing for webhook endpoints
- [ ] Implement session timeout for onboarding sessions

---

## Implementation Priority

1. **THIS WEEK:** Admin endpoint authentication (CRITICAL)
2. **THIS WEEK:** Input sanitization (HIGH)
3. **NEXT WEEK:** Move test users to database (MEDIUM)
4. **NEXT WEEK:** Add rate limiting (MEDIUM)
5. **BACKLOG:** Enhanced audit logging (LOW)
