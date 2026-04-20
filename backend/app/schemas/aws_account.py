"""AWS Account schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AWSAccountCreate(BaseModel):
    """Schema for creating a new AWS account."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    access_key_id: str = Field(..., min_length=1)
    secret_access_key: str = Field(..., min_length=1)
    sso_region: str = Field(default="us-east-2")
    kiro_region: str = Field(default="us-east-1")
    sync_interval_minutes: Optional[int] = Field(default=0, ge=0, description="自动同步间隔（分钟），0 表示不自动同步")
    is_default: bool = Field(default=False, description="是否为默认账号")
    kiro_login_url: Optional[str] = Field(None, description="Kiro 登录 URL")


class AWSAccountUpdate(BaseModel):
    """Schema for updating an AWS account."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    sso_region: Optional[str] = None
    kiro_region: Optional[str] = None
    sync_interval_minutes: Optional[int] = Field(None, ge=0)
    is_default: Optional[bool] = None
    kiro_login_url: Optional[str] = None


class AWSAccountResponse(BaseModel):
    """Schema for AWS account response."""
    id: int
    name: str
    description: Optional[str] = None
    sso_region: str
    kiro_region: str
    instance_arn: Optional[str] = None
    identity_store_id: Optional[str] = None
    status: str
    last_verified: Optional[datetime] = None
    permissions: Optional[dict] = None
    sync_interval_minutes: Optional[int] = 0
    last_synced: Optional[datetime] = None
    is_default: bool = False
    kiro_login_url: Optional[str] = None
    access_key_masked: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AWSAccountListResponse(BaseModel):
    """Schema for list of AWS accounts."""
    total: int
    accounts: List[AWSAccountResponse]


class PermissionCheck(BaseModel):
    """Schema for permission check result."""
    has_identity_center_access: bool = False
    has_kiro_access: bool = False
    errors: Optional[List[str]] = None


class AccountVerificationResponse(BaseModel):
    """Schema for account verification response."""
    account_id: int
    status: str
    instance_arn: Optional[str] = None
    identity_store_id: Optional[str] = None
    permissions: Optional[PermissionCheck] = None
    message: Optional[str] = None
