"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.auth import LoginRequest, TokenResponse, CurrentUser, RefreshTokenRequest, ChangePasswordRequest, ChangePasswordResponse
from app.services import AuthService
from app.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Login and get access/refresh tokens.
    
    Default credentials:
    - Username: admin
    - Password: admin123
    """
    auth_service = AuthService(session)
    result = await auth_service.login(request.username, request.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(session)
    result = await auth_service.refresh_tokens(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=result["expires_in"]
    )


@router.get("/me", response_model=CurrentUser)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    """Get current authenticated user."""
    return CurrentUser(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email"),
        is_active=current_user.get("is_active", True)
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout (client should discard tokens).
    
    Note: In production, implement token blacklisting for proper logout.
    """
    return {"message": "Successfully logged out"}


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Change current user's password."""
    auth_service = AuthService(session)
    
    success = auth_service.change_password(
        current_user["username"],
        request.current_password,
        request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully"
    )
