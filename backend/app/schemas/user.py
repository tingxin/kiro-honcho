"""User management schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    given_name: str = Field(..., min_length=1)
    family_name: str = Field(..., min_length=1)
    display_name: Optional[str] = None
    user_name: Optional[str] = None
    auto_subscribe: bool = True
    subscription_type: str = Field(default="Q_DEVELOPER_STANDALONE_PRO")
    send_password_reset: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    display_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    user_id: str
    user_name: str
    display_name: Optional[str] = None
    email: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    status: str
    groups: Optional[List[dict]] = None
    has_subscription: bool = False
    subscription_type: Optional[str] = None
    pending_subscription_type: Optional[str] = None
    email_verified: bool = False
    last_synced: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for list of users."""
    total: int
    users: List[UserResponse]


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    mode: str = Field(default="email", pattern="^(email|otp)$")


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    success: bool
    message: str


class EmailVerificationResponse(BaseModel):
    """Schema for email verification response."""
    success: bool
    message: str


class GroupListResponse(BaseModel):
    """Schema for group list response."""
    groups: List[dict]


class AddUserToGroupRequest(BaseModel):
    """Schema for adding user to group."""
    group_name: str


class AddUserToGroupResponse(BaseModel):
    """Schema for add user to group response."""
    success: bool
    membership_id: Optional[str] = None
    message: str
