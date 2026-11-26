"""
Services Package Initialization
Exports all service classes for the CyberSafe application
"""

from services.ai_service import AIService
from services.encryption_service import EncryptionService
from services.email_service import EmailService
from services.file_service import FileService

# List of all service classes
services = [
    AIService,
    EncryptionService,
    EmailService,
    FileService
]

__all__ = [
    'AIService',
    'EncryptionService',
    'EmailService',
    'FileService',
    'services'
]