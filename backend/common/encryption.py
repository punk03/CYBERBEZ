"""Encryption utilities."""

from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os

from backend.common.config import settings
from backend.common.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Encryption service for data at rest."""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption service.
        
        Args:
            key: Encryption key (if None, derived from SECRET_KEY)
        """
        if key:
            self.key = key
        else:
            # Derive key from SECRET_KEY
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'prokvant_salt',  # In production, use random salt stored securely
                iterations=100000,
                backend=default_backend()
            )
            self.key = base64.urlsafe_b64encode(
                kdf.derive(settings.SECRET_KEY.encode())
            )
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
        
        Returns:
            Encrypted data (base64 encoded)
        """
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}", exc_info=True)
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
        
        Returns:
            Decrypted data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}", exc_info=True)
            raise


# Global encryption service instance
encryption_service = EncryptionService()
