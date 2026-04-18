"""Authentication API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_session
from app.schemas.auth import (
    LoginRequest, TokenResponse, CurrentUser,
    RefreshTokenRequest, ChangePasswordRequest, ChangePasswordResponse,
)
from app.services import AuthService
from app.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)):
    auth_service = AuthService(session)
    result = await auth_service.login(request.username, request.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    # MFA required — return partial response
    if result.get("mfa_required"):
        return {
            "mfa_required": True,
            "user_id": result["user_id"],
            "message": "Please enter your TOTP code",
        }
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
    )


class MfaLoginRequest(BaseModel):
    user_id: int
    code: str


@router.post("/login/mfa")
async def login_mfa(request: MfaLoginRequest, session: AsyncSession = Depends(get_session)):
    """MFA 验证后完成登录."""
    auth_service = AuthService(session)
    result = await auth_service.login_with_mfa(request.user_id, request.code)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session)):
    auth_service = AuthService(session)
    result = await auth_service.refresh_tokens(request.refresh_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return TokenResponse(**result)


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email"),
        "is_active": current_user.get("is_active", True),
        "is_admin": current_user.get("is_admin", False),
        "mfa_enabled": current_user.get("mfa_enabled", False),
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    auth_service = AuthService(session)
    success = await auth_service.change_password(
        current_user["username"], request.current_password, request.new_password
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    return ChangePasswordResponse(success=True, message="Password changed successfully")


# ========== MFA ==========

class MfaCodeRequest(BaseModel):
    code: str


@router.post("/mfa/setup")
async def setup_mfa(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """生成 TOTP secret 和 QR code URI."""
    auth_service = AuthService(session)
    result = await auth_service.setup_mfa(current_user["id"])
    # 生成 QR code base64
    import qrcode, io, base64
    qr = qrcode.make(result["uri"])
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()
    return {
        "secret": result["secret"],
        "uri": result["uri"],
        "qr_code": f"data:image/png;base64,{qr_base64}",
    }


@router.post("/mfa/verify")
async def verify_mfa(
    request: MfaCodeRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """验证 TOTP code 并启用 MFA."""
    auth_service = AuthService(session)
    if await auth_service.verify_and_enable_mfa(current_user["id"], request.code):
        return {"success": True, "message": "MFA enabled"}
    raise HTTPException(status_code=400, detail="Invalid code")


@router.post("/mfa/disable")
async def disable_mfa(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """禁用 MFA."""
    auth_service = AuthService(session)
    await auth_service.disable_mfa(current_user["id"])
    return {"success": True, "message": "MFA disabled"}


# ========== 系统用户管理（仅 admin） ==========

class CreateAppUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class AppUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False


def _require_admin(current_user: dict):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("/users", response_model=List[AppUserResponse])
async def list_app_users(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)
    auth_service = AuthService(session)
    return await auth_service.list_users()


@router.post("/users", response_model=AppUserResponse, status_code=status.HTTP_201_CREATED)
async def create_app_user(
    request: CreateAppUserRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)
    auth_service = AuthService(session)
    try:
        return await auth_service.create_user(request.username, request.password, request.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_app_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)
    auth_service = AuthService(session)
    if not await auth_service.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete admin or user not found")
    return {"message": "User deleted"}


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/users/{user_id}/reset-password")
async def reset_app_user_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _require_admin(current_user)
    auth_service = AuthService(session)
    if not await auth_service.reset_password(user_id, request.new_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "Password reset"}
