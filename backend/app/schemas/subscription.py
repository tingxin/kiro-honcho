"""Subscription management schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import StrEnum


class SubscriptionType(StrEnum):
    """Kiro subscription types."""
    PRO = "Q_DEVELOPER_STANDALONE_PRO"
    PRO_PLUS = "Q_DEVELOPER_STANDALONE_PRO_PLUS"
    PRO_POWER = "Q_DEVELOPER_STANDALONE_PRO_POWER"
    # Kiro Enterprise 类型
    KIRO_PRO = "KIRO_ENTERPRISE_PRO"
    KIRO_PRO_PLUS = "KIRO_ENTERPRISE_PRO_PLUS"


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription."""
    principal_id: str
    principal_type: str = Field(default="USER")
    subscription_type: str = Field(default="Q_DEVELOPER_STANDALONE_PRO")


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription (change plan)."""
    subscription_type: str


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: int
    principal_id: str
    subscription_type: str
    status: str
    start_date: Optional[datetime] = None
    last_synced: Optional[datetime] = None
    created_at: datetime
    
    # User info (from join)
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_display_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Schema for list of subscriptions."""
    total: int
    subscriptions: List[SubscriptionResponse]


class ChangePlanRequest(BaseModel):
    """Schema for change plan request."""
    emails: List[str] = Field(..., min_items=1)
    subscription_type: str = Field(default="Q_DEVELOPER_STANDALONE_PRO_PLUS")


class ChangePlanResult(BaseModel):
    """Schema for single change plan result."""
    email: str
    success: bool
    message: str


class ChangePlanResponse(BaseModel):
    """Schema for change plan response."""
    total: int
    success_count: int
    failed_count: int
    results: List[ChangePlanResult]
