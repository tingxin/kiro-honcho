"""AWS Account database model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AWSAccount(Base):
    """AWS Account model for storing account credentials and metadata."""
    
    __tablename__ = "aws_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    access_key_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Encrypted
    secret_access_key: Mapped[str] = mapped_column(String(512), nullable=False)  # Encrypted
    
    # AWS Configuration
    sso_region: Mapped[str] = mapped_column(String(50), default="us-east-2")
    kiro_region: Mapped[str] = mapped_column(String(50), default="us-east-1")
    instance_arn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    identity_store_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, active, invalid
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 自动同步配置（分钟，0 或 None 表示不自动同步）
    sync_interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    ic_users: Mapped[List["ICUser"]] = relationship(
        "ICUser",
        back_populates="aws_account",
        cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["KiroSubscription"]] = relationship(
        "KiroSubscription",
        back_populates="aws_account",
        cascade="all, delete-orphan"
    )
    operation_logs: Mapped[List["OperationLog"]] = relationship(
        "OperationLog",
        back_populates="aws_account",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<AWSAccount(id={self.id}, name='{self.name}', status='{self.status}')>"


class ICUser(Base):
    """Identity Center User model."""
    
    __tablename__ = "ic_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aws_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # AWS Identity Center Info
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)  # AWS UserId
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    given_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    family_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="enabled")
    groups: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 自动订阅配置：用户创建时指定的待分配套餐类型
    # 当用户激活（邮箱验证完成）后，后台自动分配此套餐
    # 为空表示不需要自动订阅
    pending_subscription_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # 邮箱是否已验证（用户点击邮件链接后变为 True）
    email_verified: Mapped[bool] = mapped_column(default=False)
    
    # Sync info
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    aws_account: Mapped["AWSAccount"] = relationship("AWSAccount", back_populates="ic_users")
    subscription: Mapped[Optional["KiroSubscription"]] = relationship(
        "KiroSubscription",
        back_populates="ic_user",
        uselist=False
    )
    
    def __repr__(self):
        return f"<ICUser(id={self.id}, email='{self.email}')>"


class KiroSubscription(Base):
    """Kiro Subscription model."""
    
    __tablename__ = "kiro_subscriptions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aws_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("ic_users.id"), nullable=True)
    
    # Subscription Info
    principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_type: Mapped[str] = mapped_column(String(100), default="Q_DEVELOPER_STANDALONE_PRO")
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    aws_account: Mapped["AWSAccount"] = relationship("AWSAccount", back_populates="subscriptions")
    ic_user: Mapped["ICUser"] = relationship("ICUser", back_populates="subscription")
    
    def __repr__(self):
        return f"<KiroSubscription(id={self.id}, principal_id='{self.principal_id}')>"


class OperationLog(Base):
    """Operation Log model for tracking all operations."""
    
    __tablename__ = "operation_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aws_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # Operation Info
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, success, failed
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Operator info
    operator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    aws_account: Mapped["AWSAccount"] = relationship("AWSAccount", back_populates="operation_logs")
    
    def __repr__(self):
        return f"<OperationLog(id={self.id}, operation='{self.operation}')>"


class CreditUsage(Base):
    """Credit Usage model for tracking user credit consumption."""
    
    __tablename__ = "credit_usage"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("ic_users.id"), nullable=False)
    
    # Usage Info
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_credits: Mapped[int] = mapped_column(Integer, default=0)
    feature_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CreditUsage(id={self.id}, user_id={self.user_id}, credits={self.total_credits})>"


class BatchTask(Base):
    """Batch Task model for async operations."""
    
    __tablename__ = "batch_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aws_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("aws_accounts.id"), nullable=False)
    
    # Task Info
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    targets: Mapped[dict] = mapped_column(JSON, default=list)
    params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Progress
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BatchTask(id={self.id}, type='{self.task_type}', status='{self.status}')>"
