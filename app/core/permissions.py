"""
Permissions Module - Stub Implementation
"""
from enum import Enum
from typing import List
from fastapi import HTTPException, status
from app.models import User


class Permission(str, Enum):
    """Permission types"""
    # Campaign management
    CAMPAIGN_VIEW = "campaign:view"
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_EDIT = "campaign:edit"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_PUBLISH = "campaign:publish"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

    # AI and Optimization
    AI_CONTROL = "ai:control"
    OPTIMIZATION_MANAGE = "optimization:manage"
    AUTONOMOUS_APPROVE = "autonomous:approve"

    # User management
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"
    USER_DELETE = "user:delete"

    # Security and compliance
    SECURITY_ADMIN = "security:admin"
    AUDIT_VIEW = "audit:view"
    COMPLIANCE_MANAGE = "compliance:manage"

    # Billing
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"

    # System administration
    SYSTEM_ADMIN = "system:admin"
    SETTINGS_MANAGE = "settings:manage"


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission.
    """
    if not user or not user.is_active:
        return False

    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Check if user has wildcard permission
    if "*" in user.permissions:
        return True

    # Check for specific permission
    return permission.value in user.permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has any of the specified permissions.
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has all of the specified permissions.
    """
    return all(has_permission(user, perm) for perm in permissions)


def require_permissions(user: User, permissions: List[Permission], require_all: bool = True):
    """
    Raise HTTPException if user doesn't have required permissions.

    Args:
        user: The user to check
        permissions: List of required permissions
        require_all: If True, user must have all permissions. If False, user needs at least one.

    Raises:
        HTTPException: 403 if user lacks required permissions
    """
    if require_all:
        has_perms = has_all_permissions(user, permissions)
    else:
        has_perms = has_any_permission(user, permissions)

    if not has_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


def get_user_permissions(user: User) -> List[str]:
    """
    Get list of all permissions for a user.
    """
    if user.is_superuser or "*" in user.permissions:
        return [perm.value for perm in Permission]

    return user.permissions
