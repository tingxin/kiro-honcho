"""批量操作 API 路由 — 支持 SSE 实时进度."""
import csv
import io
import json
import asyncio
from typing import List, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session, async_session_maker
from app.models import AWSAccount, ICUser, KiroSubscription
from app.services import AccountService
from app.services.log_service import OperationLogService
from app.aws import AWSClient, IdentityCenterClient, KiroSubscriptionClient
from app.middleware import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/accounts/{account_id}/batch", tags=["Batch"])


class BatchUserItem(BaseModel):
    email: str
    given_name: str | None = None
    family_name: str | None = None
    display_name: str | None = None
    user_name: str | None = None
    subscription_type: str = "Q_DEVELOPER_STANDALONE_PRO"


class BatchCreateRequest(BaseModel):
    users: List[BatchUserItem]
    send_password_reset: bool = True


async def _process_batch_stream(
    account_id: int,
    users: List[BatchUserItem],
    send_password_reset: bool,
    operator: str,
) -> AsyncGenerator[str, None]:
    """逐个处理用户，通过 SSE 返回实时进度."""
    
    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    total = len(users)
    success_count = 0
    failed_count = 0
    
    yield _event({"type": "start", "total": total, "message": f"开始处理 {total} 个用户..."})
    
    async with async_session_maker() as session:
        account_service = AccountService(session)
        account = await account_service.get_account(account_id)
        if not account or account.status != "active":
            yield _event({"type": "error", "message": "账号不存在或未验证"})
            yield _event({"type": "done", "success_count": 0, "failed_count": total})
            return
        
        access_key, secret_key = account_service.decrypt_credentials(account)
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        kiro_client = KiroSubscriptionClient(
            aws_client, kiro_region=account.kiro_region, sso_region=account.sso_region
        )
        log_service = OperationLogService(session)
        
        for i, item in enumerate(users):
            progress = i + 1
            try:
                # Step 1: 检查用户是否已存在
                existing_id = ic_client.find_user_by_email(account.identity_store_id, item.email)
                if existing_id:
                    yield _event({
                        "type": "progress", "current": progress, "total": total,
                        "email": item.email, "step": "skip",
                        "message": f"[{progress}/{total}] {item.email} — 用户已存在",
                    })
                    success_count += 1
                    continue
                
                # Step 2: 创建 IC 用户
                yield _event({
                    "type": "progress", "current": progress, "total": total,
                    "email": item.email, "step": "creating",
                    "message": f"[{progress}/{total}] {item.email} — 创建 Identity Center 用户...",
                })
                
                given_name = item.given_name or item.email.split("@")[0]
                family_name = item.family_name or "Mr"
                display_name = item.display_name or f"{given_name} {family_name}"
                username = item.user_name or (item.given_name or item.email.split("@")[0])
                
                try:
                    user_id = ic_client.create_user(
                        identity_store_id=account.identity_store_id,
                        username=username, display_name=display_name,
                        given_name=given_name, family_name=family_name, email=item.email,
                    )
                except Exception as dup_e:
                    if "Duplicate" in str(dup_e) or "Conflict" in str(dup_e) or "duplicate" in str(dup_e):
                        username = item.email
                        user_id = ic_client.create_user(
                            identity_store_id=account.identity_store_id,
                            username=username, display_name=display_name,
                            given_name=given_name, family_name=family_name, email=item.email,
                        )
                    else:
                        raise dup_e
                
                yield _event({
                    "type": "progress", "current": progress, "total": total,
                    "email": item.email, "step": "created",
                    "message": f"[{progress}/{total}] {item.email} — ✅ IC 用户已创建",
                })
                
                # 保存到数据库
                ic_user = ICUser(
                    aws_account_id=account_id, user_id=user_id, user_name=username,
                    display_name=display_name, email=item.email,
                    given_name=given_name, family_name=family_name,
                    status="enabled", pending_subscription_type=None, email_verified=False,
                )
                session.add(ic_user)
                await session.commit()
                await session.refresh(ic_user)
                
                # Step 3: 发送邮件
                if send_password_reset:
                    ic_client.send_password_reset_email(user_id)
                    ic_client.send_email_verification(user_id, account.identity_store_id)
                    yield _event({
                        "type": "progress", "current": progress, "total": total,
                        "email": item.email, "step": "email_sent",
                        "message": f"[{progress}/{total}] {item.email} — ✅ 邮件已发送",
                    })
                
                # Step 4: 分配订阅
                yield _event({
                    "type": "progress", "current": progress, "total": total,
                    "email": item.email, "step": "subscribing",
                    "message": f"[{progress}/{total}] {item.email} — 分配 Kiro 订阅...",
                })
                
                sub_result = kiro_client.create_assignment(
                    instance_arn=account.instance_arn,
                    principal_id=user_id,
                    subscription_type=item.subscription_type,
                )
                
                if sub_result["success"]:
                    new_sub = KiroSubscription(
                        aws_account_id=account_id, user_id=ic_user.id,
                        principal_id=user_id, subscription_type=sub_result.get("actual_type", item.subscription_type),
                        status="PENDING",
                    )
                    session.add(new_sub)
                    await session.commit()
                    yield _event({
                        "type": "progress", "current": progress, "total": total,
                        "email": item.email, "step": "subscribed",
                        "message": f"[{progress}/{total}] {item.email} — ✅ 订阅已分配",
                    })
                else:
                    ic_user.pending_subscription_type = item.subscription_type
                    await session.commit()
                    yield _event({
                        "type": "progress", "current": progress, "total": total,
                        "email": item.email, "step": "sub_failed",
                        "message": f"[{progress}/{total}] {item.email} — ⚠️ 订阅分配失败，后台将重试",
                    })
                
                await log_service.log_operation(
                    account_id=account_id, operation="batch_create_user",
                    target=f"user:{item.email}", status="success",
                    message=f"批量创建: {item.email}", operator=operator,
                )
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                yield _event({
                    "type": "progress", "current": progress, "total": total,
                    "email": item.email, "step": "error",
                    "message": f"[{progress}/{total}] {item.email} — ❌ 失败: {str(e)[:100]}",
                })
            
            # 小延迟避免 API 限流
            await asyncio.sleep(0.1)
        
        yield _event({
            "type": "done",
            "success_count": success_count,
            "failed_count": failed_count,
            "message": f"完成！成功 {success_count}，失败 {failed_count}",
        })


@router.post("/users/stream")
async def batch_create_users_stream(
    account_id: int,
    request: BatchCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """批量创建用户（SSE 实时进度）."""
    operator = current_user.get("username", "unknown")
    return StreamingResponse(
        _process_batch_stream(account_id, request.users, request.send_password_reset, operator),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/users/csv/stream")
async def batch_create_users_csv_stream(
    account_id: int,
    file: UploadFile = File(...),
    send_password_reset: bool = Form(True),
    current_user: dict = Depends(get_current_user),
):
    """CSV 批量创建用户（SSE 实时进度）."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    users = []
    for row in reader:
        email = row.get("email", "").strip()
        if not email:
            continue
        users.append(BatchUserItem(
            email=email,
            given_name=row.get("given_name", "").strip() or None,
            family_name=row.get("family_name", "").strip() or None,
            display_name=row.get("display_name", "").strip() or None,
            user_name=row.get("user_name", "").strip() or None,
            subscription_type=row.get("subscription_type", "").strip() or "Q_DEVELOPER_STANDALONE_PRO",
        ))

    if not users:
        raise HTTPException(status_code=400, detail="CSV 文件中没有有效用户数据")

    operator = current_user.get("username", "unknown")
    return StreamingResponse(
        _process_batch_stream(account_id, users, send_password_reset, operator),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
