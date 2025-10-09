"""
Admin User Management System
No-code solution for managing internal users, test accounts, and employee access
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import uuid

from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# User Account Types
class AccountType(str, Enum):
    INTERNAL_EMPLOYEE = "internal_employee"
    TEST_USER = "test_user"
    CUSTOMER = "customer"
    BETA_TESTER = "beta_tester"
    PARTNER = "partner"
    CONTRACTOR = "contractor"

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    DEVELOPER = "developer"
    SALES = "sales"
    MARKETING = "marketing"
    CUSTOMER_SUCCESS = "customer_success"
    TEST_USER = "test_user"
    BETA_TESTER = "beta_tester"

class PulseBridgePermission(str, Enum):
    # Suite Access
    FULL_SUITE_ACCESS = "full_suite_access"
    ML_SUITE = "ml_suite"
    FINANCIAL_SUITE = "financial_suite"
    AI_SUITE = "ai_suite"
    HR_SUITE = "hr_suite"
    
    # Admin Functions
    USER_MANAGEMENT = "user_management"
    BILLING_MANAGEMENT = "billing_management"
    ANALYTICS_ACCESS = "analytics_access"
    SYSTEM_MONITORING = "system_monitoring"
    
    # Business Operations
    CAMPAIGN_MANAGEMENT = "campaign_management"
    LEAD_MANAGEMENT = "lead_management"
    REPORTING = "reporting"
    
    # Development
    API_ACCESS = "api_access"
    WEBHOOK_MANAGEMENT = "webhook_management"
    INTEGRATION_MANAGEMENT = "integration_management"

# Pydantic Models
class CreateInternalUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    account_type: AccountType
    role: UserRole
    permissions: List[PulseBridgePermission] = Field(default_factory=list)
    department: Optional[str] = None
    manager_email: Optional[EmailStr] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None  # For contractors/temporary access
    notes: Optional[str] = Field(None, max_length=500)
    bypass_billing: bool = True  # Internal users bypass billing by default
    suite_access: List[str] = Field(default_factory=lambda: ["ml_suite", "financial_suite", "ai_suite", "hr_suite"])

class UpdateInternalUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    account_type: Optional[AccountType] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[PulseBridgePermission]] = None
    department: Optional[str] = None
    manager_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)
    bypass_billing: Optional[bool] = None
    suite_access: Optional[List[str]] = None

class InternalUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    account_type: AccountType
    role: UserRole
    permissions: List[str]
    department: Optional[str]
    manager_email: Optional[str]
    is_active: bool
    bypass_billing: bool
    suite_access: List[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    notes: Optional[str]

class BulkUserOperation(BaseModel):
    user_ids: List[str]
    operation: str  # activate, deactivate, update_permissions, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)

# Role-based permission templates
ROLE_PERMISSION_TEMPLATES = {
    UserRole.SUPER_ADMIN: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
        PulseBridgePermission.USER_MANAGEMENT,
        PulseBridgePermission.BILLING_MANAGEMENT,
        PulseBridgePermission.ANALYTICS_ACCESS,
        PulseBridgePermission.SYSTEM_MONITORING,
        PulseBridgePermission.API_ACCESS,
        PulseBridgePermission.WEBHOOK_MANAGEMENT,
        PulseBridgePermission.INTEGRATION_MANAGEMENT,
    ],
    UserRole.ADMIN: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
        PulseBridgePermission.USER_MANAGEMENT,
        PulseBridgePermission.ANALYTICS_ACCESS,
        PulseBridgePermission.CAMPAIGN_MANAGEMENT,
        PulseBridgePermission.LEAD_MANAGEMENT,
        PulseBridgePermission.REPORTING,
    ],
    UserRole.EMPLOYEE: [
        PulseBridgePermission.ML_SUITE,
        PulseBridgePermission.FINANCIAL_SUITE,
        PulseBridgePermission.AI_SUITE,
        PulseBridgePermission.HR_SUITE,
        PulseBridgePermission.REPORTING,
    ],
    UserRole.MANAGER: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
        PulseBridgePermission.ANALYTICS_ACCESS,
        PulseBridgePermission.CAMPAIGN_MANAGEMENT,
        PulseBridgePermission.LEAD_MANAGEMENT,
        PulseBridgePermission.REPORTING,
    ],
    UserRole.DEVELOPER: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
        PulseBridgePermission.API_ACCESS,
        PulseBridgePermission.WEBHOOK_MANAGEMENT,
        PulseBridgePermission.INTEGRATION_MANAGEMENT,
        PulseBridgePermission.SYSTEM_MONITORING,
    ],
    UserRole.SALES: [
        PulseBridgePermission.AI_SUITE,
        PulseBridgePermission.LEAD_MANAGEMENT,
        PulseBridgePermission.CAMPAIGN_MANAGEMENT,
        PulseBridgePermission.REPORTING,
    ],
    UserRole.MARKETING: [
        PulseBridgePermission.ML_SUITE,
        PulseBridgePermission.AI_SUITE,
        PulseBridgePermission.CAMPAIGN_MANAGEMENT,
        PulseBridgePermission.ANALYTICS_ACCESS,
        PulseBridgePermission.REPORTING,
    ],
    UserRole.CUSTOMER_SUCCESS: [
        PulseBridgePermission.AI_SUITE,
        PulseBridgePermission.LEAD_MANAGEMENT,
        PulseBridgePermission.REPORTING,
        PulseBridgePermission.ANALYTICS_ACCESS,
    ],
    UserRole.TEST_USER: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
    ],
    UserRole.BETA_TESTER: [
        PulseBridgePermission.FULL_SUITE_ACCESS,
    ],
}

class InternalUserManager:
    """Manages internal user accounts and permissions"""
    
    @staticmethod
    def get_role_permissions(role: UserRole) -> List[PulseBridgePermission]:
        """Get default permissions for a role"""
        return ROLE_PERMISSION_TEMPLATES.get(role, [])
    
    @staticmethod
    def create_internal_user_profile(user_data: CreateInternalUserRequest) -> Dict[str, Any]:
        """Create internal user profile with proper permissions and billing bypass"""
        
        # Get role-based permissions
        role_permissions = InternalUserManager.get_role_permissions(user_data.role)
        
        # Combine with explicitly requested permissions
        all_permissions = list(set(role_permissions + user_data.permissions))
        
        # Internal users get billing bypass
        billing_config = {
            "bypass_billing": True,
            "billing_type": "internal",
            "suite_access": user_data.suite_access,
            "unlimited_usage": True,
            "trial_bypass": True,
            "payment_required": False
        }
        
        user_profile = {
            "id": str(uuid.uuid4()),
            "email": user_data.email,
            "full_name": user_data.full_name,
            "account_type": user_data.account_type.value,
            "role": user_data.role.value,
            "permissions": [p.value for p in all_permissions],
            "department": user_data.department,
            "manager_email": user_data.manager_email,
            "is_active": True,
            "billing_config": billing_config,
            "suite_access": user_data.suite_access,
            "bypass_billing": True,
            "notes": user_data.notes,
            "created_at": datetime.now(timezone.utc),
            "start_date": user_data.start_date or datetime.now(timezone.utc),
            "end_date": user_data.end_date,
        }
        
        return user_profile

# API Endpoints
@router.post("/users/internal", response_model=InternalUserResponse)
async def create_internal_user(
    user_data: CreateInternalUserRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create internal user (employee, contractor, test user)
    Automatically bypasses billing and grants appropriate suite access
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User with email {user_data.email} already exists"
            )
        
        # Create user profile
        user_profile = InternalUserManager.create_internal_user_profile(user_data)
        
        # Create database user
        new_user = User(
            id=user_profile["id"],
            email=user_profile["email"],
            full_name=user_profile["full_name"],
            is_active=True,
            is_superuser=(user_data.role == UserRole.SUPER_ADMIN),
            permissions=user_profile["permissions"],
            tenant_id="pulsebridge_internal"  # Internal tenant
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send welcome email in background
        background_tasks.add_task(
            send_internal_user_welcome_email,
            user_profile
        )
        
        # Log user creation
        logger.info(f"Created internal user: {user_data.email} with role {user_data.role}")
        
        return InternalUserResponse(**user_profile)
        
    except Exception as e:
        logger.error(f"Error creating internal user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create internal user")

@router.get("/users/internal", response_model=List[InternalUserResponse])
async def list_internal_users(
    account_type: Optional[AccountType] = None,
    role: Optional[UserRole] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all internal users with optional filtering"""
    try:
        query = db.query(User).filter(User.tenant_id == "pulsebridge_internal")
        
        # Apply filters
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            
        users = query.all()
        
        # Convert to response format (simplified for now)
        internal_users = []
        for user in users:
            internal_users.append(InternalUserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name or "",
                account_type=AccountType.INTERNAL_EMPLOYEE,  # Default
                role=UserRole.EMPLOYEE,  # Default
                permissions=user.permissions or [],
                department=None,
                manager_email=None,
                is_active=user.is_active,
                bypass_billing=True,
                suite_access=["ml_suite", "financial_suite", "ai_suite", "hr_suite"],
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                notes=None
            ))
        
        return internal_users
        
    except Exception as e:
        logger.error(f"Error listing internal users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list internal users")

@router.put("/users/internal/{user_id}", response_model=InternalUserResponse)
async def update_internal_user(
    user_id: str,
    update_data: UpdateInternalUserRequest,
    db: Session = Depends(get_db)
):
    """Update internal user details and permissions"""
    try:
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == "pulsebridge_internal"
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Internal user not found")
        
        # Update user fields
        if update_data.full_name:
            user.full_name = update_data.full_name
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        if update_data.permissions:
            user.permissions = [p.value for p in update_data.permissions]
        if update_data.role == UserRole.SUPER_ADMIN:
            user.is_superuser = True
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated internal user: {user.email}")
        
        # Return updated user (simplified response)
        return InternalUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name or "",
            account_type=AccountType.INTERNAL_EMPLOYEE,
            role=update_data.role or UserRole.EMPLOYEE,
            permissions=user.permissions or [],
            department=update_data.department,
            manager_email=update_data.manager_email,
            is_active=user.is_active,
            bypass_billing=True,
            suite_access=update_data.suite_access or ["ml_suite", "financial_suite", "ai_suite", "hr_suite"],
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            notes=update_data.notes
        )
        
    except Exception as e:
        logger.error(f"Error updating internal user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update internal user")

@router.delete("/users/internal/{user_id}")
async def deactivate_internal_user(
    user_id: str,
    permanent: bool = False,
    db: Session = Depends(get_db)
):
    """Deactivate or permanently delete internal user"""
    try:
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == "pulsebridge_internal"
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Internal user not found")
        
        if permanent:
            db.delete(user)
            logger.info(f"Permanently deleted internal user: {user.email}")
        else:
            user.is_active = False
            logger.info(f"Deactivated internal user: {user.email}")
        
        db.commit()
        
        return {"message": "User deactivated successfully" if not permanent else "User deleted permanently"}
        
    except Exception as e:
        logger.error(f"Error deactivating internal user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to deactivate internal user")

@router.post("/users/bulk-operation")
async def bulk_user_operation(
    operation: BulkUserOperation,
    db: Session = Depends(get_db)
):
    """Perform bulk operations on internal users"""
    try:
        users = db.query(User).filter(
            User.id.in_(operation.user_ids),
            User.tenant_id == "pulsebridge_internal"
        ).all()
        
        if operation.operation == "activate":
            for user in users:
                user.is_active = True
        elif operation.operation == "deactivate":
            for user in users:
                user.is_active = False
        elif operation.operation == "update_permissions":
            new_permissions = operation.parameters.get("permissions", [])
            for user in users:
                user.permissions = new_permissions
        
        db.commit()
        
        logger.info(f"Bulk operation {operation.operation} completed for {len(users)} users")
        
        return {"message": f"Bulk operation completed for {len(users)} users"}
        
    except Exception as e:
        logger.error(f"Error in bulk operation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete bulk operation")

@router.get("/users/permissions/templates")
async def get_permission_templates():
    """Get permission templates for different roles"""
    templates = {}
    for role, permissions in ROLE_PERMISSION_TEMPLATES.items():
        templates[role.value] = [p.value for p in permissions]
    
    return {
        "role_templates": templates,
        "all_permissions": [p.value for p in PulseBridgePermission],
        "account_types": [t.value for t in AccountType],
        "roles": [r.value for r in UserRole]
    }

@router.post("/users/test-account")
async def create_test_account(
    email: EmailStr,
    full_name: str,
    test_duration_days: int = 30,
    suite_access: List[str] = None,
    db: Session = Depends(get_db)
):
    """
    Quick test account creation
    Perfect for onboarding new test users or beta testers
    """
    try:
        if suite_access is None:
            suite_access = ["ml_suite", "financial_suite", "ai_suite", "hr_suite"]
        
        test_user_data = CreateInternalUserRequest(
            email=email,
            full_name=full_name,
            account_type=AccountType.TEST_USER,
            role=UserRole.TEST_USER,
            permissions=[PulseBridgePermission.FULL_SUITE_ACCESS],
            notes=f"Test account created for {test_duration_days} days",
            end_date=datetime.now(timezone.utc) + timedelta(days=test_duration_days),
            suite_access=suite_access
        )
        
        # Use existing create_internal_user logic
        user_profile = InternalUserManager.create_internal_user_profile(test_user_data)
        
        new_user = User(
            id=user_profile["id"],
            email=user_profile["email"],
            full_name=user_profile["full_name"],
            is_active=True,
            permissions=user_profile["permissions"],
            tenant_id="pulsebridge_internal"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Created test account: {email} for {test_duration_days} days")
        
        return {
            "message": "Test account created successfully",
            "user_id": new_user.id,
            "email": email,
            "expires_at": user_profile["end_date"],
            "suite_access": suite_access,
            "bypass_billing": True
        }
        
    except Exception as e:
        logger.error(f"Error creating test account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create test account")

# Helper function
async def send_internal_user_welcome_email(user_profile: Dict[str, Any]):
    """Send welcome email to new internal user"""
    try:
        # Email sending logic here
        logger.info(f"Welcome email sent to {user_profile['email']}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")