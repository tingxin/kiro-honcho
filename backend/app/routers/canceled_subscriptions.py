"""已取消订阅查询 API（跨 AWS 账号）."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_session
from app.models import AWSAccount
from app.services import AccountService
from app.aws import AWSClient, IdentityCenterClient, KiroSubscriptionClient
from app.middleware import get_current_user

router = APIRouter(prefix="/canceled-subscriptions", tags=["Canceled Subscriptions"])


class CanceledSubscriptionItem(BaseModel):
    account_id: int
    account_name: str
    principal_id: str
    subscription_type: str
    status: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None


class CanceledSubscriptionListResponse(BaseModel):
    total: int
    subscriptions: List[CanceledSubscriptionItem]


@router.get("", response_model=CanceledSubscriptionListResponse)
async def list_canceled_subscriptions(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """查询所有已取消的订阅（跨 AWS 账号，实时从 AWS 查询）."""
    account_service = AccountService(session)

    # 获取所有 active 账号
    query = select(AWSAccount).where(AWSAccount.status == "active")
    result = await session.execute(query)
    accounts = list(result.scalars().all())

    canceled = []

    for account in accounts:
        try:
            access_key, secret_key = account_service.decrypt_credentials(account)
            aws_client = AWSClient(access_key, secret_key, account.sso_region)
            ic_client = IdentityCenterClient(aws_client, account.sso_region)
            kiro_client = KiroSubscriptionClient(
                aws_client,
                kiro_region=account.kiro_region,
                sso_region=account.sso_region,
            )

            subs_result = kiro_client.list_subscriptions(account.instance_arn)
            if not subs_result["success"]:
                continue

            # 构建 user_id -> user_info 缓存
            user_cache = {}

            for sub in subs_result["subscriptions"]:
                sub_status = sub.get("status", "")
                if sub_status.upper() not in ("CANCELED", "CANCELLED"):
                    continue

                principal_id = sub.get("principal", {}).get("user", "")
                sub_type = sub.get("type", {}).get("amazonQ", "")

                # 查用户信息（带缓存）
                email = ""
                uname = ""
                if principal_id and principal_id not in user_cache:
                    user_info = ic_client.get_user_by_id(
                        account.identity_store_id, principal_id
                    )
                    user_cache[principal_id] = user_info
                
                user_info = user_cache.get(principal_id)
                if user_info:
                    email = user_info.get("Email", "")
                    uname = user_info.get("UserName", "")

                canceled.append(CanceledSubscriptionItem(
                    account_id=account.id,
                    account_name=account.name,
                    principal_id=principal_id,
                    subscription_type=sub_type,
                    status=sub_status,
                    user_email=email or None,
                    user_name=uname or None,
                ))

        except Exception:
            continue

    return CanceledSubscriptionListResponse(
        total=len(canceled),
        subscriptions=canceled,
    )
