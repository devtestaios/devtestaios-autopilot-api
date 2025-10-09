# 🎯 User Access Tiers & Billing Bypass

## **Overview**

PulseBridge has **three distinct user access tiers** for billing bypass, each with different capabilities and limitations:

1. **INTERNAL** - PulseBridge employees (full access, no limits)
2. **EXTERNAL_TEST** - Third-party testers (limited access, 30 days)
3. **BETA** - Early access customers (moderate access, 90 days)

---

## **TIER 1: INTERNAL (PulseBridge Employees)**

### **Who Gets This:**
- Anyone with `@pulsebridge.ai` email
- Anyone with `@20n1.ai` email
- Anyone with `@20n1digital.com` email
- Users created via admin panel with `account_type: "internal_employee"`
- Contractors with `account_type: "contractor"`

### **Access Level: FULL ACCESS**

| Feature | Limit |
|---------|-------|
| **Suite Access** | All 4 suites (ML, Financial, AI, HR) |
| **API Calls** | Unlimited |
| **Storage** | Unlimited |
| **Team Members** | Unlimited |
| **Campaigns** | Unlimited |
| **Expiration** | Never expires |
| **Support** | Priority + white-glove |
| **Analytics** | Advanced analytics enabled |
| **Integrations** | Custom integrations allowed |

### **Billing:**
- ✅ Bypass billing completely
- ✅ No payment required ever
- ✅ Full platform access immediately
- ✅ No trial period needed

### **Use Cases:**
- PulseBridge employees testing features
- Internal operations (using PulseBridge as own CRM/ERP)
- Development and QA testing
- Customer success team demos

### **How to Add:**
```bash
# Via admin panel
POST /api/v1/admin/users/internal
{
  "email": "employee@pulsebridge.ai",
  "full_name": "John Doe",
  "account_type": "internal_employee",
  "role": "employee"
}

# Automatic: Just use @pulsebridge.ai email during signup
```

---

## **TIER 2: EXTERNAL_TEST (Third-Party Testers)**

### **Who Gets This:**
- Third-party testers added by admin
- External agencies testing the platform
- Prospective partners evaluating features
- User research participants

### **Access Level: LIMITED**

| Feature | Limit |
|---------|-------|
| **Suite Access** | 2 suites only (ML + Financial) |
| **API Calls** | 1,000/month |
| **Storage** | 1GB |
| **Team Members** | 3 max |
| **Campaigns** | 5 max |
| **Expiration** | **30 days** ⏰ |
| **Support** | Standard support only |
| **Analytics** | Basic analytics only |
| **Integrations** | Standard integrations only |

### **Billing:**
- ✅ Bypass billing for 30 days
- ⚠️ **Trial expires in 30 days**
- ⚠️ Must upgrade to paid plan after expiration
- ❌ No automatic renewal

### **Use Cases:**
- External user testing sessions
- Short-term partner evaluations
- Customer trial before purchase
- Market research participants

### **How to Add:**
```bash
# Admin only
POST /api/v1/billing/bypass/add-external-test-user?user_email=tester@example.com

# Response shows limits
{
  "user_email": "tester@example.com",
  "user_type": "external_test_user",
  "access_level": "LIMITED",
  "expires_in_days": 30,
  "suite_access": ["ml_suite", "financial_suite"],
  "limits": {
    "api_calls": "1,000/month",
    "storage": "1GB",
    "team_members": 3,
    "campaigns": 5
  }
}
```

### **Warning Messages for External Users:**
```
⚠️ Trial expires in 30 days. Contact sales for extended access.
```

---

## **TIER 3: BETA (Early Access Customers)**

### **Who Gets This:**
- Beta program participants
- Early access customers
- Strategic partners
- Launch partners

### **Access Level: MODERATE**

| Feature | Limit |
|---------|-------|
| **Suite Access** | 3 suites (ML + Financial + AI) |
| **API Calls** | 5,000/month |
| **Storage** | 5GB |
| **Team Members** | 5 max |
| **Campaigns** | 20 max |
| **Expiration** | **90 days** ⏰ |
| **Support** | Priority support ⭐ |
| **Analytics** | Advanced analytics enabled ⭐ |
| **Integrations** | Standard integrations |

### **Billing:**
- ✅ Bypass billing for 90 days
- ⚠️ **Trial expires in 90 days**
- ⚠️ Must upgrade or renew after expiration
- ✅ Can extend beta period (admin decision)

### **Special Perks:**
- ✅ Early access to new features
- ✅ Priority support channel
- ✅ Direct feedback to product team
- ✅ Beta community access
- ✅ White-glove onboarding

### **Use Cases:**
- Beta program participants
- Early adopter customers
- Strategic partnership testing
- Pre-launch customer feedback

### **How to Add:**
```bash
# Admin only
POST /api/v1/billing/bypass/add-beta-tester?user_email=beta@company.com

# Response shows benefits
{
  "user_email": "beta@company.com",
  "user_type": "beta_tester",
  "access_level": "MODERATE",
  "expires_in_days": 90,
  "suite_access": ["ml_suite", "financial_suite", "ai_suite"],
  "limits": {
    "api_calls": "5,000/month",
    "storage": "5GB",
    "team_members": 5,
    "campaigns": 20
  },
  "perks": [
    "Early access to new features",
    "Priority support",
    "Direct feedback channel"
  ]
}
```

---

## **Comparison Table**

| Feature | INTERNAL | EXTERNAL_TEST | BETA | PAID CUSTOMER |
|---------|----------|---------------|------|---------------|
| **Suites** | 4 (All) | 2 (ML, Financial) | 3 (ML, Financial, AI) | Varies by plan |
| **API Calls** | Unlimited | 1,000/mo | 5,000/mo | Varies by plan |
| **Storage** | Unlimited | 1GB | 5GB | Varies by plan |
| **Team Size** | Unlimited | 3 | 5 | Varies by plan |
| **Campaigns** | Unlimited | 5 | 20 | Varies by plan |
| **Duration** | Forever | 30 days | 90 days | Subscription |
| **Support** | Priority | Standard | Priority | Varies by plan |
| **Analytics** | Advanced | Basic | Advanced | Varies by plan |
| **Payment** | Never | After trial | After trial | Required |

---

## **API Endpoints**

### **Add Users**

```bash
# Add external test user (30-day limited trial)
POST /api/v1/billing/bypass/add-external-test-user?user_email=test@example.com
Authorization: Bearer <admin-token>

# Add beta tester (90-day moderate trial)
POST /api/v1/billing/bypass/add-beta-tester?user_email=beta@company.com
Authorization: Bearer <admin-token>

# Create internal employee (unlimited)
POST /api/v1/admin/users/internal
Authorization: Bearer <admin-token>
{
  "email": "employee@pulsebridge.ai",
  "full_name": "Employee Name",
  "account_type": "internal_employee",
  "role": "employee"
}
```

### **Remove Users**

```bash
# Remove external test user
DELETE /api/v1/billing/bypass/remove-external-test-user?user_email=test@example.com
Authorization: Bearer <admin-token>

# Remove beta tester
DELETE /api/v1/billing/bypass/remove-beta-tester?user_email=beta@company.com
Authorization: Bearer <admin-token>
```

### **List Users**

```bash
# List all bypass users (grouped by type)
GET /api/v1/billing/bypass/all-users
Authorization: Bearer <admin-token>

# Response
{
  "internal_domains": ["pulsebridge.ai", "20n1.ai", "20n1digital.com"],
  "external_test_users": {
    "emails": ["test1@example.com", "test2@example.com"],
    "count": 2,
    "access_level": "LIMITED",
    "expires_in": "30 days"
  },
  "beta_testers": {
    "emails": ["beta1@company.com"],
    "count": 1,
    "access_level": "MODERATE",
    "expires_in": "90 days"
  },
  "total_bypass_users": 3
}
```

---

##  **User Experience Differences**

### **Internal User Login:**
1. Signs up with `john@pulsebridge.ai`
2. Immediately recognized as internal
3. Demo mode badge: "🏢 PulseBridge Internal"
4. Full onboarding wizard (for testing)
5. No payment step shown
6. Direct to dashboard with all 4 suites
7. No expiration warnings

### **External Test User Login:**
1. Admin adds `tester@example.com` to external test list
2. User signs up normally
3. Demo mode badge: "🧪 30-Day Test Access"
4. Full onboarding wizard shown
5. Only 2 suites available
6. Warning: "Trial expires in 30 days"
7. Limited dashboard features
8. Expiration countdown visible

### **Beta Tester Login:**
1. Admin adds `beta@company.com` to beta list
2. User signs up normally
3. Demo mode badge: "⭐ Beta Tester"
4. Enhanced onboarding with beta perks
5. 3 suites available
6. Warning: "Beta expires in 90 days"
7. Priority support badge
8. Early access features highlighted

---

## **Best Practices**

### **For Internal Users:**
- Use company email domains
- Create via admin panel for contractors
- No limits - use freely for testing
- Report bugs directly to dev team

### **For External Test Users:**
- Use for short-term evaluations only
- Monitor usage limits
- Extend if needed (contact sales)
- 30 days is firm - plan accordingly

### **For Beta Testers:**
- Provide regular feedback
- Test new features actively
- Use priority support channel
- Consider upgrading before 90-day expiration

---

## **Upgrading/Downgrading**

### **External Test → Beta:**
```bash
# Remove from external test
DELETE /api/v1/billing/bypass/remove-external-test-user?user_email=user@example.com

# Add to beta
POST /api/v1/billing/bypass/add-beta-tester?user_email=user@example.com
```

### **Beta → Paid Customer:**
- Beta expiration triggers normal checkout flow
- Can manually upgrade anytime via dashboard
- Billing system takes over after bypass expires

### **External → Paid Customer:**
- After 30 days, normal payment required
- Can upgrade early via dashboard
- Trial period counts toward first month

---

## **Monitoring & Alerts**

### **Admin Dashboard Should Show:**
- List of all external test users with days remaining
- List of all beta testers with days remaining
- Expired trials needing follow-up
- Usage statistics per tier
- Conversion rates (test → paid, beta → paid)

### **Automated Alerts:**
- 7 days before external test expires
- 14 days before beta expires
- Day of expiration
- Follow-up 3 days after expiration

---

## **FAQ**

**Q: Can external test users access all 4 suites?**
A: No, external test users only get 2 suites (ML + Financial). Beta testers get 3 suites. Only internal users get all 4.

**Q: What happens after trial expires?**
A: For external/beta users, billing bypass ends and normal payment flow begins. They'll see a checkout page to continue using the platform.

**Q: Can we extend external test access beyond 30 days?**
A: Yes, but requires admin action. Either upgrade to beta (90 days) or add custom expiration via admin override.

**Q: Do internal users ever expire?**
A: No, internal users (@pulsebridge.ai emails) have unlimited access forever.

**Q: Can a user be both external test and beta?**
A: No, they can only be in one tier. Beta supersedes external test. Latest addition wins.

---

## **Migration from Old System**

If you had `TEST_USER_EMAILS` before:
- Existing emails moved to `EXTERNAL_TEST_USER_EMAILS`
- All get 30-day expiration from migration date
- Review and upgrade important users to beta tier
- Internal employees should use company emails

---

**This tiered system gives you precise control over who can access what, for how long!** 🎯
