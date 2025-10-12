# 🚀 Quick Start: Admin Authentication

## **Environment Variables (Set in Render)**

```bash
ADMIN_SECRET_KEY=<generate-with-command-below>
ADMIN_PASSWORD=YourSecurePassword123!
```

**Generate Secret Key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## **Step 1: Get Admin Token**

### **Development (Test Token)**
```bash
curl https://your-api.onrender.com/api/v1/auth/admin/test-token
```

### **Production (Login)**
```bash
curl -X POST https://your-api.onrender.com/api/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@pulsebridge.ai",
    "password": "your-admin-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "email": "admin@pulsebridge.ai",
  "role": "super_admin",
  "expires_in": 86400
}
```

---

## **Step 2: Use Token**

**All admin requests need:**
```
Authorization: Bearer <your-access-token>
```

---

## **Common Admin Operations**

### **1. Create Internal Employee**

```bash
curl -X POST https://your-api.onrender.com/api/v1/admin/users/internal \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employee@pulsebridge.ai",
    "full_name": "John Doe",
    "account_type": "internal_employee",
    "role": "employee",
    "department": "Engineering"
  }'
```

### **2. Create Test Account**

```bash
curl -X POST https://your-api.onrender.com/api/v1/admin/users/test-account \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tester@example.com",
    "full_name": "Test User",
    "test_duration_days": 30
  }'
```

### **3. List All Internal Users**

```bash
curl -X GET https://your-api.onrender.com/api/v1/admin/users/internal \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **4. Add Email to Billing Bypass**

```bash
curl -X POST "https://your-api.onrender.com/api/v1/billing/bypass/add-test-user?user_email=test@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **5. List Billing Bypass Users**

```bash
curl -X GET https://your-api.onrender.com/api/v1/billing/bypass/test-users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## **Authorized Admin Emails**

Default authorized admins (can be customized in `app/auth.py`):
- admin@pulsebridge.ai
- admin@20n1.ai
- admin@20n1digital.com

To add more, edit `AUTHORIZED_ADMIN_EMAILS` in `app/auth.py`.

---

## **Testing the Deployment**

### **1. Health Check**
```bash
curl https://your-api.onrender.com/health
```

### **2. Test Login (Should Work)**
```bash
curl -X POST https://your-api.onrender.com/api/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@pulsebridge.ai", "password": "your-password"}'
```

### **3. Test Protected Endpoint Without Token (Should Fail 401)**
```bash
curl -X GET https://your-api.onrender.com/api/v1/admin/users/internal
# Expected: 401 Unauthorized
```

### **4. Test Protected Endpoint With Token (Should Work 200)**
```bash
TOKEN="<your-token-from-login>"
curl -X GET https://your-api.onrender.com/api/v1/admin/users/internal \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 OK
```

---

## **Troubleshooting**

### **"Missing authorization header"**
- Add `Authorization: Bearer <token>` header to request

### **"Token has expired"**
- Tokens expire after 24 hours
- Login again to get new token

### **"Email not authorized for admin access"**
- Email must be in `AUTHORIZED_ADMIN_EMAILS` list
- Check `app/auth.py` line 16-20

### **"Invalid authentication token"**
- Token might be malformed
- Make sure to include "Bearer " prefix
- Get fresh token from login endpoint

---

## **Frontend Integration**

```javascript
// 1. Login and store token
async function adminLogin(email, password) {
  const response = await fetch('https://your-api.onrender.com/api/v1/auth/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();
  localStorage.setItem('adminToken', data.access_token);
  return data;
}

// 2. Use token for admin requests
async function createInternalUser(userData) {
  const token = localStorage.getItem('adminToken');

  const response = await fetch('https://your-api.onrender.com/api/v1/admin/users/internal', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(userData)
  });

  return response.json();
}

// 3. Check if user is admin
async function verifyAdminToken() {
  const token = localStorage.getItem('adminToken');

  const response = await fetch('https://your-api.onrender.com/api/v1/auth/admin/verify', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();
  return data.valid;
}
```

---

## **Security Best Practices**

✅ **DO:**
- Set strong `ADMIN_PASSWORD` (16+ chars, mix of letters/numbers/symbols)
- Use 32+ character `ADMIN_SECRET_KEY`
- Rotate admin password every 90 days
- Use HTTPS for all requests
- Store tokens securely (httpOnly cookies for web apps)
- Log out when done (clear token from storage)

❌ **DON'T:**
- Share admin tokens
- Commit tokens or passwords to git
- Use simple passwords like "password123"
- Use the test token endpoint in production
- Store tokens in localStorage (prefer httpOnly cookies)
- Hardcode credentials in frontend code

---

## **Next Steps**

After deployment works:
1. Test admin login
2. Create your first internal user
3. Verify billing bypass still works for internal users
4. Set up Redis for session management (see `PERFORMANCE_ENHANCEMENTS.md`)
5. Write unit tests (see `TESTING_STRATEGY.md`)
6. Add bcrypt password hashing (see `SECURITY_ENHANCEMENTS_NEEDED.md`)
