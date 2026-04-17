"""操作日志 schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OperationLogResponse(BaseModel):
    """操作日志响应."""
    id: int
    aws_account_id: int
    operation: str
    target: str
    status: str
    message: Optional[str] = None
    details: Optional[dict] = None
    operator: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OperationLogListResponse(BaseModel):
    """操作日志列表响应."""
    total: int
    logs: List[OperationLogResponse]
