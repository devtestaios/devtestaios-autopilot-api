"""
Database Models - Stub Implementation
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional, List
from datetime import datetime


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    tenant_id = Column(String)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime)

    def __repr__(self):
        return f"<User(email='{self.email}')>"


class TenantConfig(Base):
    """Tenant configuration model"""
    __tablename__ = "tenant_configs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    settings = Column(JSON, default=dict)
    encrypted = Column(Boolean, default=True)
    backup_status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<TenantConfig(tenant_id='{self.tenant_id}')>"


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String)
    user_id = Column(String)
    action = Column(String, nullable=False)
    resource_type = Column(String)
    resource_id = Column(String)
    risk_level = Column(String, default="LOW")
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', risk_level='{self.risk_level}')>"


class Campaign(Base):
    """Campaign model"""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    status = Column(String, default="draft")
    budget = Column(Float)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<Campaign(name='{self.name}', platform='{self.platform}')>"
