"""操作日志服务."""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import OperationLog


class OperationLogService:
    """操作日志服务."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_operation(
        self,
        account_id: int,
        operation: str,
        target: str,
        status: str = "success",
        message: Optional[str] = None,
        details: Optional[dict] = None,
        operator: Optional[str] = None,
    ) -> OperationLog:
        """记录一条操作日志."""
        log = OperationLog(
            aws_account_id=account_id,
            operation=operation,
            target=target,
            status=status,
            message=message,
            details=details,
            operator=operator,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_logs(
        self,
        account_id: int,
        skip: int = 0,
        limit: int = 50,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[int, List[OperationLog]]:
        """查询日志列表，支持过滤."""
        base = select(OperationLog).where(OperationLog.aws_account_id == account_id)

        if operation:
            base = base.where(OperationLog.operation == operation)
        if status:
            base = base.where(OperationLog.status == status)
        if start_date:
            base = base.where(OperationLog.created_at >= start_date)
        if end_date:
            base = base.where(OperationLog.created_at <= end_date)

        total = await self.session.scalar(select(func.count()).select_from(base.subquery()))

        query = base.offset(skip).limit(limit).order_by(OperationLog.created_at.desc())
        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        return total, logs

    async def get_log(self, account_id: int, log_id: int) -> Optional[OperationLog]:
        """获取单条日志."""
        query = select(OperationLog).where(
            OperationLog.id == log_id,
            OperationLog.aws_account_id == account_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
