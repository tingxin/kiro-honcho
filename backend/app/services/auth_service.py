"""Authentication service for internal app users."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils import create_access_token, create_refresh_token, decode_token
from app.config import get_settings

settings = get_settings()

# Simple in-memory user store for development
# In production, this should be replaced with a database table
_DEMO_USERS: Dict[str, Dict[str, Any]] = {}

def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def _init_demo_users():
    """Initialize demo users with hashed passwords."""
    if not _DEMO_USERS:
        _DEMO_USERS["admin"] = {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": _hash_password("admin123"),  # Default password
            "is_active": True
        }


class AuthService:
    """Authentication service."""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return _verify_password(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return _hash_password(password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        For now, uses in-memory demo user.
        In production, query from database.
        """
        _init_demo_users()  # Ensure users are initialized
        user = _DEMO_USERS.get(username)
        if not user:
            return None
        
        if not self.verify_password(password, user["hashed_password"]):
            return None
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_active": user["is_active"]
        }
    
    async def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Login and generate tokens.
        
        Returns:
            Dict with access_token, refresh_token, and user info
        """
        user = await self.authenticate_user(username, password)
        if not user:
            return None
        
        token_data = {"sub": str(user["id"]), "username": user["username"]}
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token pair
        """
        payload = decode_token(refresh_token)
        if not payload:
            return None
        
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            return None
        
        # In production, check if user still exists and is active
        # user = await self.get_user_by_id(user_id)
        # if not user or not user.is_active:
        #     return None
        
        token_data = {"sub": user_id, "username": username}
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    async def get_current_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get current user by ID."""
        _init_demo_users()  # Ensure users are initialized
        # In production, query from database
        for user in _DEMO_USERS.values():
            if user["id"] == user_id:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "is_active": user["is_active"]
                }
        return None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        _init_demo_users()  # Ensure users are initialized
        user = _DEMO_USERS.get(username)
        if not user:
            return False
        
        if not self.verify_password(old_password, user["hashed_password"]):
            return False
        
        user["hashed_password"] = self.hash_password(new_password)
        return True
