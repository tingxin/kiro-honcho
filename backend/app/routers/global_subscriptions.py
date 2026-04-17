"""全局订阅查询 API（跨 AWS 账号）."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import AWSAccount, ICUser, KiroSubscription
from app.schemas.subscription import SubscriptionResponse, SubscriptionListResponse
from app.middleware import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["Global Subscriptions"])


@router.get("", response_model=SubscriptionListResponse)
async def list_all_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    account_id: Optional[int] = Query(None, description="按 AWS 账号筛选"),
    subscription_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """查询所有活跃订阅（跨 AWS 账号），支持按账号筛选."""
    base_query = select(KiroSubscription)

    if account_id:
        base_query = base_query.where(KiroSubscription.aws_account_id == account_id)
    if subscription_type:
        base_query = base_query.where(KiroSubscription.subscription_type == subscription_type)

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = await session.scalar(count_query)

    # Get subscriptions
    query = base_query.offset(skip).limit(limit).order_by(KiroSubscription.created_at.desc())
    result = await session.execute(query)
    subscriptions = list(result.scalars().all())

    # 批量加载关联的用户和账号信息
    # 收集所有需要的 account_id 和 user_id
    account_ids = set(s.aws_account_id for s in subscriptions)
    user_ids = set(s.user_id for s in subscriptions if s.user_id)

    # 查询账号
    account_map = {}
    if account_ids:
        acc_result = await session.execute(select(AWSAccount).where(AWSAccount.id.in_(account_ids)))
        for acc in acc_result.scalars().all():
            account_map[acc.id] = acc

    # 查询用户
    user_map = {}
    if user_ids:
        user_result = await session.execute(select(ICUser).where(ICUser.id.in_(user_ids)))
        for u in user_result.scalars().all():
            user_map[u.id] = u

    responses = []
    for sub in subscriptions:
        user = user_map.get(sub.user_id)
        account = account_map.get(sub.aws_account_id)
        responses.append(SubscriptionResponse(
            id=sub.id,
            principal_id=sub.principal_id,
            subscription_type=sub.subscription_type,
            status=sub.status,
            start_date=sub.start_date,
            last_synced=sub.last_synced,
            created_at=sub.created_at,
            user_email=user.email if user else None,
            user_name=user.user_name if user else None,
            user_display_name=user.display_name if user else None,
            account_id=sub.aws_account_id,
            account_name=account.name if account else None,
        ))

    return SubscriptionListResponse(total=total or 0, subscriptions=responses)
