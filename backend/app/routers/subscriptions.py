"""Subscription management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_session
from app.models import AWSAccount, ICUser, KiroSubscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionListResponse,
    ChangePlanRequest,
    ChangePlanResult,
    ChangePlanResponse
)
from app.services import AccountService
from app.services.log_service import OperationLogService
from app.aws import AWSClient, KiroSubscriptionClient
from app.middleware import get_current_user

router = APIRouter(prefix="/accounts/{account_id}/subscriptions", tags=["Subscriptions"])


def _get_sub_response(sub: KiroSubscription, user: Optional[ICUser] = None) -> SubscriptionResponse:
    """Helper to create SubscriptionResponse."""
    return SubscriptionResponse(
        id=sub.id,
        principal_id=sub.principal_id,
        subscription_type=sub.subscription_type,
        status=sub.status,
        start_date=sub.start_date,
        last_synced=sub.last_synced,
        created_at=sub.created_at,
        user_email=user.email if user else None,
        user_name=user.user_name if user else None,
        user_display_name=user.display_name if user else None
    )


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    account_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subscription_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """List subscriptions for an AWS account."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Build query
    base_query = select(KiroSubscription).where(
        KiroSubscription.aws_account_id == account_id
    )
    
    if subscription_type:
        base_query = base_query.where(
            KiroSubscription.subscription_type == subscription_type
        )
    
    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = await session.scalar(count_query)
    
    # Get subscriptions with user join
    query = base_query.offset(skip).limit(limit).order_by(
        KiroSubscription.created_at.desc()
    )
    result = await session.execute(query)
    subscriptions = list(result.scalars().all())
    
    # Get user info
    responses = []
    for sub in subscriptions:
        user = None
        if sub.user_id:
            user_query = select(ICUser).where(ICUser.id == sub.user_id)
            user = await session.scalar(user_query)
        responses.append(_get_sub_response(sub, user))
    
    return SubscriptionListResponse(total=total, subscriptions=responses)


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    account_id: int,
    request: SubscriptionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Create a new Kiro subscription."""
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
        kiro_client = KiroSubscriptionClient(
            aws_client,
            kiro_region=account.kiro_region,
            sso_region=account.sso_region
        )
        
        # Create assignment
        result = kiro_client.create_assignment(
            instance_arn=account.instance_arn,
            principal_id=request.principal_id,
            principal_type=request.principal_type,
            subscription_type=request.subscription_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to create subscription")
            )
        
        # Find user by principal_id
        user_query = select(ICUser).where(
            ICUser.aws_account_id == account_id,
            ICUser.user_id == request.principal_id
        )
        ic_user = await session.scalar(user_query)
        
        # Save to database
        subscription = KiroSubscription(
            aws_account_id=account_id,
            user_id=ic_user.id if ic_user else None,
            principal_id=request.principal_id,
            subscription_type=request.subscription_type,
            status="active"
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        
        # 记录创建订阅日志
        log_service = OperationLogService(session)
        operator = current_user.get("email") if current_user else None
        await log_service.log_operation(
            account_id=account_id,
            operation="create_subscription",
            target=f"subscription:{request.principal_id}",
            status="success",
            message=f"成功创建订阅: {request.principal_id} -> {request.subscription_type}",
            details={"principal_id": request.principal_id, "subscription_type": request.subscription_type},
            operator=operator,
        )
        
        return _get_sub_response(subscription, ic_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    account_id: int,
    subscription_id: int,
    request: SubscriptionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Change subscription plan."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get subscription
    query = select(KiroSubscription).where(
        KiroSubscription.id == subscription_id,
        KiroSubscription.aws_account_id == account_id
    )
    subscription = await session.scalar(query)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        kiro_client = KiroSubscriptionClient(
            aws_client,
            kiro_region=account.kiro_region,
            sso_region=account.sso_region
        )
        
        # Update assignment
        result = kiro_client.update_assignment(
            principal_id=subscription.principal_id,
            subscription_type=request.subscription_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to update subscription")
            )
        
        # Update database
        old_type = subscription.subscription_type
        subscription.subscription_type = request.subscription_type
        await session.commit()
        await session.refresh(subscription)
        
        # 记录更改计划日志
        log_service = OperationLogService(session)
        operator = current_user.get("email") if current_user else None
        await log_service.log_operation(
            account_id=account_id,
            operation="change_plan",
            target=f"subscription:{subscription.principal_id}",
            status="success",
            message=f"成功更改计划: {old_type} -> {request.subscription_type}",
            details={
                "principal_id": subscription.principal_id,
                "old_plan": old_type,
                "new_plan": request.subscription_type,
            },
            operator=operator,
        )
        
        # Get user
        user = None
        if subscription.user_id:
            user_query = select(ICUser).where(ICUser.id == subscription.user_id)
            user = await session.scalar(user_query)
        
        return _get_sub_response(subscription, user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.delete("/{subscription_id}")
async def delete_subscription(
    account_id: int,
    subscription_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Cancel/delete a subscription."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    # Get subscription
    query = select(KiroSubscription).where(
        KiroSubscription.id == subscription_id,
        KiroSubscription.aws_account_id == account_id
    )
    subscription = await session.scalar(query)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        kiro_client = KiroSubscriptionClient(
            aws_client,
            kiro_region=account.kiro_region,
            sso_region=account.sso_region
        )
        
        # Delete assignment
        result = kiro_client.delete_assignment(
            instance_arn=account.instance_arn,
            principal_id=subscription.principal_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to delete subscription")
            )
        
        # 记录删除订阅日志
        principal_id = subscription.principal_id
        log_service = OperationLogService(session)
        operator = current_user.get("email") if current_user else None
        await log_service.log_operation(
            account_id=account_id,
            operation="delete_subscription",
            target=f"subscription:{principal_id}",
            status="success",
            message=f"成功取消订阅: {principal_id}",
            operator=operator,
        )
        
        # Delete from database
        await session.delete(subscription)
        await session.commit()
        
        return {"message": f"Subscription {subscription_id} cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subscription: {str(e)}"
        )


@router.post("/change-plan", response_model=ChangePlanResponse)
async def batch_change_plan(
    account_id: int,
    request: ChangePlanRequest,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Batch change subscription plans for multiple users."""
    account_service = AccountService(session)
    account = await account_service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    access_key, secret_key = account_service.decrypt_credentials(account)
    
    results = []
    success_count = 0
    failed_count = 0
    
    try:
        aws_client = AWSClient(access_key, secret_key, account.sso_region)
        kiro_client = KiroSubscriptionClient(
            aws_client,
            kiro_region=account.kiro_region,
            sso_region=account.sso_region
        )
        
        for email in request.emails:
            try:
                # Find user by email
                user_query = select(ICUser).where(
                    ICUser.aws_account_id == account_id,
                    ICUser.email == email.lower()
                )
                ic_user = await session.scalar(user_query)
                
                if not ic_user:
                    results.append(ChangePlanResult(
                        email=email,
                        success=False,
                        message=f"User not found"
                    ))
                    failed_count += 1
                    continue
                
                # Find subscription
                sub_query = select(KiroSubscription).where(
                    KiroSubscription.user_id == ic_user.id
                )
                subscription = await session.scalar(sub_query)
                
                if not subscription:
                    results.append(ChangePlanResult(
                        email=email,
                        success=False,
                        message="User has no subscription"
                    ))
                    failed_count += 1
                    continue
                
                # Update
                result = kiro_client.update_assignment(
                    principal_id=subscription.principal_id,
                    subscription_type=request.subscription_type
                )
                
                if result["success"]:
                    subscription.subscription_type = request.subscription_type
                    success_count += 1
                    results.append(ChangePlanResult(
                        email=email,
                        success=True,
                        message=f"Changed to {request.subscription_type}"
                    ))
                else:
                    failed_count += 1
                    results.append(ChangePlanResult(
                        email=email,
                        success=False,
                        message=result.get("message", "Update failed")
                    ))
                    
            except Exception as e:
                failed_count += 1
                results.append(ChangePlanResult(
                    email=email,
                    success=False,
                    message=str(e)
                ))
        
        await session.commit()
        
        return ChangePlanResponse(
            total=len(request.emails),
            success_count=success_count,
            failed_count=failed_count,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch operation failed: {str(e)}"
        )
