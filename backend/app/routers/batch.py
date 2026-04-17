"""批量操作 API 路由."""
import csv
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models import AWSAccount, ICUser, KiroSubscription
from app.services import AccountService
from app.services.log_service import OperationLogService
from app.aws import AWSClient, IdentityCenterClient
from app.middleware import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/accounts/{account_id}/batch", tags=["Batch"])


class BatchUserItem(BaseModel):
    email: str
    given_name: str
    family_name: str
    display_name: str | None = None
    user_name: str | None = None
    subscription_type: str = "Q_DEVELOPER_STANDALONE_PRO"


class BatchCreateRequest(BaseModel):
    users: List[BatchUserItem]
    send_password_reset: bool = True


class BatchResultItem(BaseModel):
    email: str
    success: bool
    message: str


class BatchCreateResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: List[BatchResultItem]


@router.post("/users", response_model=BatchCreateResponse)
async def batch_create_users(
    account_id: int,
    request: BatchCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """批量创建用户并设置自动订阅.
    
    用户创建后会发送密码重置邮件，用户激活后系统自动分配 Kiro 订阅。
    """
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.status != "active":
        raise HTTPException(status_code=400, detail="Account not verified")

    access_key, secret_key = account_service.decrypt_credentials(account)
    aws_client = AWSClient(access_key, secret_key, account.sso_region)
    ic_client = IdentityCenterClient(aws_client, account.sso_region)

    results = []
    success_count = 0
    failed_count = 0
    log_service = OperationLogService(session)
    operator = current_user.get("username", "unknown")

    for item in request.users:
        try:
            # 检查用户是否已存在
            existing_id = ic_client.find_user_by_email(
                account.identity_store_id, item.email
            )
            if existing_id:
                # 用户已存在，检查是否已在本地数据库
                query = select(ICUser).where(
                    ICUser.aws_account_id == account_id,
                    ICUser.user_id == existing_id,
                )
                local_user = await session.scalar(query)
                if local_user and not local_user.pending_subscription_type:
                    # 设置待订阅
                    local_user.pending_subscription_type = item.subscription_type
                    await session.commit()
                results.append(BatchResultItem(
                    email=item.email,
                    success=True,
                    message=f"用户已存在，已设置自动订阅 ({item.subscription_type})",
                ))
                success_count += 1
                continue

            # 创建 IC 用户
            username = item.user_name or item.email.split("@")[0]
            display_name = item.display_name or f"{item.given_name} {item.family_name}"

            user_id = ic_client.create_user(
                identity_store_id=account.identity_store_id,
                username=username,
                display_name=display_name,
                given_name=item.given_name,
                family_name=item.family_name,
                email=item.email,
            )

            # 保存到数据库
            ic_user = ICUser(
                aws_account_id=account_id,
                user_id=user_id,
                user_name=username,
                display_name=display_name,
                email=item.email,
                given_name=item.given_name,
                family_name=item.family_name,
                status="enabled",
                pending_subscription_type=None,
                email_verified=False,
            )
            session.add(ic_user)
            await session.commit()
            await session.refresh(ic_user)

            # 发送密码重置邮件和邮箱验证邮件
            if request.send_password_reset:
                ic_client.send_password_reset_email(user_id)
                ic_client.send_email_verification(user_id, account.identity_store_id)

            # 立即分配订阅（AWS 会设为 PENDING，用户验证后自动变 ACTIVE）
            from app.aws import KiroSubscriptionClient
            kiro_client = KiroSubscriptionClient(
                aws_client,
                kiro_region=account.kiro_region,
                sso_region=account.sso_region,
            )
            sub_result = kiro_client.create_assignment(
                instance_arn=account.instance_arn,
                principal_id=user_id,
                subscription_type=item.subscription_type,
            )
            sub_msg = ""
            if sub_result["success"]:
                from app.models import KiroSubscription
                new_sub = KiroSubscription(
                    aws_account_id=account_id,
                    user_id=ic_user.id,
                    principal_id=user_id,
                    subscription_type=item.subscription_type,
                    status="PENDING",
                )
                session.add(new_sub)
                await session.commit()
                sub_msg = f"，订阅已分配 (PENDING)"
            else:
                # 分配失败，设置 pending 让后台重试
                ic_user.pending_subscription_type = item.subscription_type
                await session.commit()
                sub_msg = f"，订阅分配失败，后台将重试"

            await log_service.log_operation(
                account_id=account_id,
                operation="batch_create_user",
                target=f"user:{item.email}",
                status="success",
                message=f"批量创建用户: {item.email}{sub_msg}",
                operator=operator,
            )

            results.append(BatchResultItem(
                email=item.email,
                success=True,
                message=f"已创建{sub_msg}",
            ))
            success_count += 1

        except Exception as e:
            failed_count += 1
            results.append(BatchResultItem(
                email=item.email,
                success=False,
                message=str(e),
            ))

    return BatchCreateResponse(
        total=len(request.users),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )


@router.post("/users/csv", response_model=BatchCreateResponse)
async def batch_create_users_csv(
    account_id: int,
    file: UploadFile = File(...),
    send_password_reset: bool = Form(True),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """通过 CSV 文件批量创建用户.
    
    CSV 格式: email,given_name,family_name,subscription_type(可选)
    第一行为表头。
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")

    content = await file.read()
    text = content.decode("utf-8-sig")  # 支持 BOM
    reader = csv.DictReader(io.StringIO(text))

    users = []
    for row in reader:
        email = row.get("email", "").strip()
        if not email:
            continue
        users.append(BatchUserItem(
            email=email,
            given_name=row.get("given_name", row.get("name", "")).strip() or email.split("@")[0],
            family_name=row.get("family_name", "").strip() or "User",
            display_name=row.get("display_name", "").strip() or None,
            user_name=row.get("user_name", "").strip() or None,
            subscription_type=row.get("subscription_type", "").strip() or "Q_DEVELOPER_STANDALONE_PRO",
        ))

    if not users:
        raise HTTPException(status_code=400, detail="CSV 文件中没有有效用户数据")

    # 复用 batch_create_users 的逻辑
    request = BatchCreateRequest(users=users, send_password_reset=send_password_reset)
    return await batch_create_users(account_id, request, session, current_user)
