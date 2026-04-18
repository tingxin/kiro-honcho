"""Authentication service — database-backed with TOTP MFA."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import bcrypt
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import AppUser
from app.utils import create_access_token, create_refresh_token, decode_token
from app.config import get_settings

settings = get_settings()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _ensure_default_admin(self):
        """首次启动时创建默认 admin 用户."""
        query = select(AppUser).where(AppUser.username == settings.DEFAULT_ADMIN_USERNAME)
        existing = await self.session.scalar(query)
        if not existing:
            admin = AppUser(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email="admin@example.com",
                hashed_password=_hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                is_active=True,
                is_admin=True,
            )
            self.session.add(admin)
            await self.session.commit()

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        await self._ensure_default_admin()
        query = select(AppUser).where(AppUser.username == username)
        user = await self.session.scalar(query)
        if not user or not _verify_password(password, user.hashed_password):
            return None
        return {"id": user.id, "username": user.username, "email": user.email, "is_active": user.is_active, "is_admin": user.is_admin, "mfa_enabled": user.mfa_enabled}

    async def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = await self.authenticate_user(username, password)
        if not user:
            return None
        
        # 如果启用了 MFA，返回 mfa_required 标记，不发 token
        if user.get("mfa_enabled"):
            return {
                "mfa_required": True,
                "user_id": user["id"],
                "username": user["username"],
            }
        
        token_data = {"sub": str(user["id"]), "username": user["username"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }

    async def login_with_mfa(self, user_id: int, code: str) -> Optional[Dict[str, Any]]:
        """MFA 验证后完成登录."""
        user = await self.get_current_user(user_id)
        if not user:
            return None
        if not await self.verify_totp(user_id, code):
            return None
        token_data = {"sub": str(user["id"]), "username": user["username"]}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }

    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        username = payload.get("username")
        if not user_id or not username:
            return None
        token_data = {"sub": user_id, "username": username}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def get_current_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = select(AppUser).where(AppUser.id == user_id)
        user = await self.session.scalar(query)
        if not user:
            return None
        return {"id": user.id, "username": user.username, "email": user.email, "is_active": user.is_active, "is_admin": user.is_admin, "mfa_enabled": user.mfa_enabled}

    async def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        query = select(AppUser).where(AppUser.username == username)
        user = await self.session.scalar(query)
        if not user or not _verify_password(old_password, user.hashed_password):
            return False
        user.hashed_password = _hash_password(new_password)
        await self.session.commit()
        return True

    async def list_users(self) -> List[Dict[str, Any]]:
        result = await self.session.execute(select(AppUser).order_by(AppUser.id))
        return [
            {"id": u.id, "username": u.username, "email": u.email, "is_active": u.is_active, "is_admin": u.is_admin, "mfa_enabled": u.mfa_enabled}
            for u in result.scalars().all()
        ]

    async def create_user(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        existing = await self.session.scalar(select(AppUser).where(AppUser.username == username))
        if existing:
            raise ValueError(f"用户 {username} 已存在")
        user = AppUser(username=username, email=email, hashed_password=_hash_password(password), is_active=True)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return {"id": user.id, "username": user.username, "email": user.email, "is_active": user.is_active}

    async def delete_user(self, user_id: int) -> bool:
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def reset_password(self, user_id: int, new_password: str) -> bool:
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user:
            return False
        user.hashed_password = _hash_password(new_password)
        await self.session.commit()
        return True

    async def setup_mfa(self, user_id: int) -> Dict[str, str]:
        """生成 TOTP secret 和 QR code URI，返回给前端显示."""
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user:
            raise ValueError("User not found")
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.mfa_enabled = False  # 还没验证，先不启用
        await self.session.commit()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.username, issuer_name="Kiro Honcho")
        return {"secret": secret, "uri": uri}

    async def verify_and_enable_mfa(self, user_id: int, code: str) -> bool:
        """验证 TOTP code 并启用 MFA."""
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user or not user.totp_secret:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            user.mfa_enabled = True
            await self.session.commit()
            return True
        return False

    async def disable_mfa(self, user_id: int) -> bool:
        """禁用 MFA."""
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user:
            return False
        user.mfa_enabled = False
        user.totp_secret = None
        await self.session.commit()
        return True

    async def verify_totp(self, user_id: int, code: str) -> bool:
        """验证 TOTP code（登录时）."""
        user = await self.session.scalar(select(AppUser).where(AppUser.id == user_id))
        if not user or not user.totp_secret:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)
