"""AWS Account management API routes."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.aws_account import (
    AWSAccountCreate,
    AWSAccountUpdate,
    AWSAccountResponse,
    AWSAccountListResponse,
    AccountVerificationResponse
)
from app.services import AccountService
from app.utils import get_encryption_service
from app.middleware import get_current_user

router = APIRouter(prefix="/accounts", tags=["AWS Accounts"])


def _mask_key(encrypted_key: str) -> str:
    """解密 AK 后掩码：前4位 + ****** + 后4位."""
    try:
        enc = get_encryption_service()
        plain = enc.decrypt(encrypted_key)
        if len(plain) <= 10:
            return plain[:2] + "******" + plain[-2:]
        return plain[:4] + "******" + plain[-4:]
    except Exception:
        return "******"


def _account_response(acc) -> AWSAccountResponse:
    """构建账号响应，含掩码 AK."""
    resp = AWSAccountResponse.model_validate(acc)
    resp.access_key_masked = _mask_key(acc.access_key_id)
    return resp


@router.get("/stats")
async def get_dashboard_stats(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics."""
    service = AccountService(session)
    return await service.get_dashboard_stats(account_id)


@router.get("", response_model=AWSAccountListResponse)
async def list_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """List all AWS accounts."""
    service = AccountService(session)
    total, accounts = await service.list_accounts(skip, limit)
    
    return AWSAccountListResponse(
        total=total,
        accounts=[_account_response(acc) for acc in accounts]
    )


@router.post("", response_model=AWSAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AWSAccountCreate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Add a new AWS account."""
    service = AccountService(session)
    
    # Check if account with same name exists
    # In production, add duplicate check
    
    account = await service.create_account(
        name=request.name,
        access_key_id=request.access_key_id,
        secret_access_key=request.secret_access_key,
        sso_region=request.sso_region,
        kiro_region=request.kiro_region,
        description=request.description,
        sync_interval_minutes=request.sync_interval_minutes or 0,
        is_default=request.is_default if hasattr(request, 'is_default') else False,
    )
    
    return _account_response(account)


@router.get("/{account_id}", response_model=AWSAccountResponse)
async def get_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific AWS account."""
    service = AccountService(session)
    account = await service.get_account(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    return _account_response(account)


@router.put("/{account_id}", response_model=AWSAccountResponse)
async def update_account(
    account_id: int,
    request: AWSAccountUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Update an AWS account."""
    service = AccountService(session)
    account = await service.update_account(
        account_id=account_id,
        name=request.name,
        description=request.description,
        access_key_id=request.access_key_id,
        secret_access_key=request.secret_access_key,
        sso_region=request.sso_region,
        kiro_region=request.kiro_region,
        sync_interval_minutes=request.sync_interval_minutes,
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    return _account_response(account)


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Delete an AWS account."""
    service = AccountService(session)
    success = await service.delete_account(account_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AWS account {account_id} not found"
        )
    
    return {"message": f"AWS account {account_id} deleted"}


@router.post("/{account_id}/verify", response_model=AccountVerificationResponse)
async def verify_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Verify AWS account credentials and permissions."""
    service = AccountService(session)
    result = await service.verify_account(account_id)
    
    return AccountVerificationResponse(
        account_id=result["account_id"],
        status=result.get("status", "invalid"),
        instance_arn=result.get("instance_arn"),
        identity_store_id=result.get("identity_store_id"),
        permissions=result.get("permissions"),
        message=result.get("message")
    )


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Sync users and subscriptions from AWS account."""
    service = AccountService(session)
    result = await service.sync_account_data(account_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Sync failed")
        )
    
    # 更新 last_synced
    service_for_update = AccountService(session)
    account = await service_for_update.get_account(account_id)
    if account:
        from datetime import timezone
        account.last_synced = datetime.now(timezone.utc)
        await session.commit()
    
    return {
        "message": "Sync completed",
        "synced_users": result.get("synced_users", 0),
        "synced_subscriptions": result.get("synced_subscriptions", 0)
    }
