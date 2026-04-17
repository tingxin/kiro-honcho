"""Credit and batch operation schemas."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Credit schemas
class CreditSummary(BaseModel):
    """Schema for credit summary."""
    total_credits: int
    total_users: int
    active_users: int
    average_per_user: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class CreditUserUsage(BaseModel):
    """Schema for single user credit usage."""
    user_id: int
    user_email: str
    user_name: Optional[str] = None
    total_credits: int
    last_active: Optional[datetime] = None


class CreditUsageListResponse(BaseModel):
    """Schema for list of user credit usage."""
    total: int
    usage: List[CreditUserUsage]


class CreditTrendPoint(BaseModel):
    """Schema for credit trend data point."""
    date: date
    credits: int
    users: int


class CreditTrendResponse(BaseModel):
    """Schema for credit trend response."""
    data: List[CreditTrendPoint]


class CreditBreakdown(BaseModel):
    """Schema for credit breakdown by feature."""
    feature: str
    credits: int
    percentage: float


class CreditBreakdownResponse(BaseModel):
    """Schema for credit breakdown response."""
    total: int
    breakdown: List[CreditBreakdown]


# Batch operation schemas
class BatchCreateUsersRequest(BaseModel):
    """Schema for batch create users request."""
    users: List[Dict[str, Any]] = Field(..., min_items=1)
    auto_subscribe: bool = True
    subscription_type: str = Field(default="Q_DEVELOPER_STANDALONE_PRO")
    send_password_reset: bool = True


class BatchChangePlanRequest(BaseModel):
    """Schema for batch change plan request."""
    emails: List[str] = Field(..., min_items=1)
    subscription_type: str = Field(default="Q_DEVELOPER_STANDALONE_PRO_PLUS")


class BatchTaskStatus(BaseModel):
    """Schema for batch task status."""
    id: int
    task_type: str
    status: str
    progress: int
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class BatchTaskListResponse(BaseModel):
    """Schema for list of batch tasks."""
    total: int
    tasks: List[BatchTaskStatus]
