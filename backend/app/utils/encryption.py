"""Encryption utilities for storing AWS credentials."""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import get_settings


class EncryptionService:
    """AES-256-GCM encryption service for sensitive data."""
    
    def __init__(self):
        self._key = self._derive_key()
        self._aesgcm = AESGCM(self._key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from master key."""
        settings = get_settings()
        
        if not settings.APP_ENCRYPTION_KEY:
            # Generate a key from SECRET_KEY if no encryption key
            # This is less secure but works for development
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"kiro-honcho-salt",
                iterations=100000,
                backend=default_backend()
            )
            return kdf.derive(settings.SECRET_KEY.encode())
        
        # Use provided encryption key (should be base64 encoded 32 bytes)
        try:
            key = base64.b64decode(settings.APP_ENCRYPTION_KEY)
            if len(key) != 32:
                raise ValueError("Encryption key must be 32 bytes")
            return key
        except Exception:
            raise ValueError("Invalid APP_ENCRYPTION_KEY, must be base64 encoded 32-byte key")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Returns:
            Base64 encoded string with format: nonce(12) + ciphertext + tag(16)
        """
        if not plaintext:
            return ""
        
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted string.
        
        Args:
            encrypted: Base64 encoded encrypted string
            
        Returns:
            Original plaintext string
        """
        if not encrypted:
            return ""
        
        try:
            data = base64.b64decode(encrypted)
            nonce = data[:12]
            ciphertext = data[12:]
            return self._aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to decrypt: {e}")


# Singleton instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get encryption service singleton."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
