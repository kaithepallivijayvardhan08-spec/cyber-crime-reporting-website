from cryptography.fernet import Fernet, InvalidToken
from config import Config

TEXT_PREFIX = 'CSENC1:'
BYTES_PREFIX = b'CSENC1:'

class EncryptionService:
    """Service for data encryption and decryption"""

    def __init__(self):
        if not Config.DATA_ENCRYPTION_KEY:
            raise RuntimeError('DATA_ENCRYPTION_KEY must be configured before starting CyberSafe')
        try:
            self.cipher = Fernet(Config.DATA_ENCRYPTION_KEY.encode('ascii'))
        except (ValueError, UnicodeEncodeError) as exc:
            raise RuntimeError('DATA_ENCRYPTION_KEY is invalid') from exc

    def encrypt_data(self, data):
        """Encrypt text while leaving already-versioned ciphertext unchanged."""
        if data is None:
            return None
        if not isinstance(data, str):
            raise TypeError('Text encryption requires a string')
        if data.startswith(TEXT_PREFIX):
            return data
        return TEXT_PREFIX + self.cipher.encrypt(data.encode('utf-8')).decode('ascii')

    def decrypt_data(self, encrypted_data):
        """Decrypt versioned text; unmarked values are legacy plaintext."""
        if encrypted_data is None or not isinstance(encrypted_data, str):
            return encrypted_data
        if not encrypted_data.startswith(TEXT_PREFIX):
            return encrypted_data
        try:
            token = encrypted_data[len(TEXT_PREFIX):].encode('ascii')
            return self.cipher.decrypt(token).decode('utf-8')
        except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError) as exc:
            raise ValueError('Encrypted text could not be authenticated') from exc

    def encrypt_bytes(self, data):
        """Encrypt binary data for evidence storage."""
        if not isinstance(data, bytes):
            raise TypeError('Binary encryption requires bytes')
        if data.startswith(BYTES_PREFIX):
            return data
        return BYTES_PREFIX + self.cipher.encrypt(data)

    def decrypt_bytes(self, data):
        """Decrypt evidence bytes; unmarked files are legacy plaintext."""
        if not data.startswith(BYTES_PREFIX):
            return data
        try:
            return self.cipher.decrypt(data[len(BYTES_PREFIX):])
        except InvalidToken as exc:
            raise ValueError('Evidence could not be authenticated') from exc

    @staticmethod
    def hash_sensitive_data(data):
        """Create hash of sensitive data for comparison"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_sensitive_info(text, show_chars=4, mask_char='*'):
        """Mask sensitive information like credit cards, emails"""
        if not text:
            return text
        
        # Email masking
        if '@' in text:
            local, domain = text.split('@')
            if len(local) > show_chars:
                masked_local = local[:show_chars] + mask_char * (len(local) - show_chars)
            else:
                masked_local = mask_char * len(local)
            return f"{masked_local}@{domain}"
        
        # Phone number masking
        if text.isdigit() and len(text) == 10:
            return mask_char * 6 + text[-4:]
        
        # General text masking
        if len(text) > show_chars * 2:
            return text[:show_chars] + mask_char * (len(text) - show_chars * 2) + text[-show_chars:]
        
        return mask_char * len(text)
