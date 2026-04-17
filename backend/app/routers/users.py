"""User management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import AWSAccount, ICUser, KiroSubscription
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    EmailVerificationResponse,
    GroupListResponse,
    AddUserToGroupRequest,
    AddUserToGroupResponse
)
from app.services import AccountService
from app.services.log_service import OperationLogService
from app.aws import AWSClient, IdentityCenterClient
from app.middleware import get_current_user

router = APIRouter(prefix="/accounts/{account_id}/users", tags=["Users"])


def _get_user_response(user: ICUser) -> UserResponse:
    """Helper to create UserResponse from ICUser."""
    return UserResponse(
        id=user.id,
        user_id=user.user_id,
        user_name=user.user_name,
        display_name=user.display_name,
        email=user.email,
        given_name=user.given_name,
        family_name=user.family_name,
        status=user.status,
        groups=user.groups,
        has_subscription=bool(user.subscription),
        subscription_type=user.subscription.subscription_type if user.subscription else None,
        pending_subscription_type=user.pending_subscription_type,
        email_verified=user.email_verified if user.email_verified else False,
        last_synced=user.last_synced,
        created_at=user.created_at
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    account_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by email or name"),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """List users for an AWS account."""
    # Verify account exists
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Build query
    base_query = select(ICUser).where(ICUser.aws_account_id == account_id)
    
    if search:
        base_query = base_query.where(
            ICUser.email.ilike(f"%{search}%") |
            ICUser.display_name.ilike(f"%{search}%") |
            ICUser.user_name.ilike(f"%{search}%")
        )
    
    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = await session.scalar(count_query)
    
    # Get users with subscription eagerly loaded
    query = base_query.options(selectinload(ICUser.subscription)).offset(skip).limit(limit).order_by(ICUser.created_at.desc())
    result = await session.execute(query)
    users = list(result.scalars().all())
    
    return UserListResponse(
        total=total,
        users=[_get_user_response(u) for u in users]
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    account_id: int,
    request: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user in Identity Center."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    if account.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account not verified"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        # Check if user exists
        existing = ic_client.find_user_by_email(account.identity_store_id, request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {request.email} already exists"
            )
        
        # Create user
        username = request.user_name or request.email.split("@")[0]
        display_name = request.display_name or f"{request.given_name} {request.family_name}"
        
        user_id = ic_client.create_user(
            identity_store_id=account.identity_store_id,
            username=username,
            display_name=display_name,
            given_name=request.given_name,
            family_name=request.family_name,
            email=request.email
        )
        
        # Save to database
        ic_user = ICUser(
            aws_account_id=account_id,
            user_id=user_id,
            user_name=username,
            display_name=display_name,
            email=request.email,
            given_name=request.given_name,
            family_name=request.family_name,
            status="enabled",
            email_verified=False,
            pending_subscription_type=None,  # 立即分配，不需要 pending
        )
        session.add(ic_user)
        await session.commit()
        await session.refresh(ic_user)
        
        # 记录创建用户日志
        log_service = OperationLogService(session)
        operator = current_user.get("email") if current_user else None
        await log_service.log_operation(
            account_id=account_id,
            operation="create_user",
            target=f"user:{request.email}",
            status="success",
            message=f"成功创建用户: {request.email}",
            details={"user_id": user_id, "user_name": username},
            operator=operator,
        )
        
        # Send password reset email if requested
        if request.send_password_reset:
            ic_client.send_password_reset_email(user_id)
            # 同时发送邮箱验证邮件
            ic_client.send_email_verification(user_id, account.identity_store_id)
        
        # 立即分配订阅（AWS 会将状态设为 PENDING，用户验证邮箱后自动变为 ACTIVE）
        if request.auto_subscribe:
            from app.aws import KiroSubscriptionClient
            kiro_client = KiroSubscriptionClient(
                aws_client,
                kiro_region=account.kiro_region,
                sso_region=account.sso_region
            )
            sub_result = kiro_client.create_assignment(
                instance_arn=account.instance_arn,
                principal_id=user_id,
                subscription_type=request.subscription_type
            )
            
            if sub_result["success"]:
                from app.models import KiroSubscription
                subscription = KiroSubscription(
                    aws_account_id=account_id,
                    user_id=ic_user.id,
                    principal_id=user_id,
                    subscription_type=request.subscription_type,
                    status="PENDING"
                )
                session.add(subscription)
                await session.commit()
                await session.refresh(ic_user)
            else:
                # 分配失败，设置 pending 让后台重试
                ic_user.pending_subscription_type = request.subscription_type
                await session.commit()
        
        # 重新查询用户（含 subscription 关联），避免 lazy loading 问题
        refreshed_query = select(ICUser).options(selectinload(ICUser.subscription)).where(ICUser.id == ic_user.id)
        ic_user = await session.scalar(refreshed_query)
        return _get_user_response(ic_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    account_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user."""
    query = select(ICUser).options(selectinload(ICUser.subscription)).where(
        ICUser.id == user_id,
        ICUser.aws_account_id == account_id
    )
    user = await session.scalar(query)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return _get_user_response(user)


@router.delete("/{user_id}")
async def delete_user(
    account_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user from Identity Center."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get user from database
    query = select(ICUser).where(
        ICUser.id == user_id,
        ICUser.aws_account_id == account_id
    )
    ic_user = await session.scalar(query)
    
    if not ic_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        # Step 1: 先取消 Kiro 订阅
        sub_query = select(KiroSubscription).where(
            KiroSubscription.aws_account_id == account_id,
            KiroSubscription.principal_id == ic_user.user_id,
        )
        subscription = await session.scalar(sub_query)
        
        if subscription:
            from app.aws import KiroSubscriptionClient
            kiro_client = KiroSubscriptionClient(
                aws_client,
                kiro_region=account.kiro_region,
                sso_region=account.sso_region,
            )
            del_sub_result = kiro_client.delete_assignment(
                instance_arn=account.instance_arn,
                principal_id=ic_user.user_id,
                subscription_type=subscription.subscription_type,
            )
            if not del_sub_result["success"]:
                # 尝试不指定 subscription_type 删除
                kiro_client.delete_assignment(
                    instance_arn=account.instance_arn,
                    principal_id=ic_user.user_id,
                )
            # 删除本地订阅记录
            await session.delete(subscription)
            await session.flush()
        
        # Step 2: 再从 Identity Center 删除用户
        ic_client.delete_user(account.identity_store_id, ic_user.user_id)
        
        # 记录删除用户日志
        user_email = ic_user.email
        log_service = OperationLogService(session)
        operator = current_user.get("email") if current_user else None
        await log_service.log_operation(
            account_id=account_id,
            operation="delete_user",
            target=f"user:{user_email}",
            status="success",
            message=f"成功删除用户: {user_email}（已取消订阅并从 Identity Center 移除）",
            operator=operator,
        )
        
        # 删除本地用户记录
        await session.delete(ic_user)
        await session.commit()
        
        return {"message": f"User {user_id} deleted (subscription cancelled, removed from Identity Center)"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    account_id: int,
    user_id: int,
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Send password reset email to user."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get user
    query = select(ICUser).where(
        ICUser.id == user_id,
        ICUser.aws_account_id == account_id
    )
    ic_user = await session.scalar(query)
    
    if not ic_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        if request.mode == "otp":
            result = ic_client.send_password_reset_otp(ic_user.user_id)
        else:
            result = ic_client.send_password_reset_email(ic_user.user_id)
        
        return PasswordResetResponse(
            success=result["success"],
            message=result["message"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset: {str(e)}"
        )


@router.post("/{user_id}/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    account_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Send email verification to user."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get user
    query = select(ICUser).where(
        ICUser.id == user_id,
        ICUser.aws_account_id == account_id
    )
    ic_user = await session.scalar(query)
    
    if not ic_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        result = ic_client.send_email_verification(
            ic_user.user_id,
            account.identity_store_id
        )
        
        return EmailVerificationResponse(
            success=result["success"],
            message=result["message"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification: {str(e)}"
        )


@router.get("/groups", response_model=GroupListResponse)
async def list_groups(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """List all groups in Identity Center."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        groups = ic_client.list_groups(account.identity_store_id)
        
        return GroupListResponse(groups=groups)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list groups: {str(e)}"
        )


@router.post("/{user_id}/add-to-group", response_model=AddUserToGroupResponse)
async def add_user_to_group(
    account_id: int,
    user_id: int,
    request: AddUserToGroupRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Add user to a group."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get user
    query = select(ICUser).where(
        ICUser.id == user_id,
        ICUser.aws_account_id == account_id
    )
    ic_user = await session.scalar(query)
    
    if not ic_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        ic_client = IdentityCenterClient(aws_client, account.sso_region)
        
        # Get group ID
        group_id = ic_client.get_group_id_by_name(
            account.identity_store_id,
            request.group_name
        )
        
        if not group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group '{request.group_name}' not found"
            )
        
        membership_id = ic_client.add_user_to_group(
            account.identity_store_id,
            ic_user.user_id,
            group_id
        )
        
        return AddUserToGroupResponse(
            success=True,
            membership_id=membership_id,
            message=f"User added to group {request.group_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add user to group: {str(e)}"
        )
