"""操作日志 API 路由."""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.log import OperationLogResponse, OperationLogListResponse
from app.services.log_service import OperationLogService
from app.services import AccountService
from app.middleware import get_current_user

router = APIRouter(prefix="/accounts/{account_id}/logs", tags=["Logs"])


@router.get("", response_model=OperationLogListResponse)
async def list_logs(
    account_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    operation: Optional[str] = Query(None),
    log_status: Optional[str] = Query(None, alias="status"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """查询操作日志列表."""
    # 验证账号存在
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AWS account {account_id} not found")

    log_service = OperationLogService(session)
    total, logs = await log_service.list_logs(
        account_id=account_id,
        skip=skip,
        limit=limit,
        operation=operation,
        status=log_status,
        start_date=start_date,
        end_date=end_date,
    )
    return OperationLogListResponse(total=total, logs=logs)


@router.get("/{log_id}", response_model=OperationLogResponse)
async def get_log(
    account_id: int,
    log_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """获取单条日志详情."""
    log_service = OperationLogService(session)
    log = await log_service.get_log(account_id, log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Log {log_id} not found")
    return log
