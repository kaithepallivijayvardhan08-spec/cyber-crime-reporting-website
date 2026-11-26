import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'dev-secret-key-change-in-production'
    )
    DEBUG = os.getenv('FLASK_ENV') == 'development'

    # JWT
    JWT_SECRET_KEY = os.getenv(
        'JWT_SECRET_KEY',
        'jwt-secret-key-change'
    )
    DATA_ENCRYPTION_KEY = os.getenv('DATA_ENCRYPTION_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'cybersafe_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))

    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # File upload
    MAX_CONTENT_LENGTH = int(
        os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    )
    UPLOAD_FOLDER = os.getenv(
        'UPLOAD_FOLDER',
        'uploads/evidences'
    )
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'txt'}

    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')

    # Email
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ADMIN_EMAIL = os.getenv(
        'ADMIN_EMAIL',
        'admin@cybersafe.gov.in'
    )

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')
    RATELIMIT_STORAGE_URL = os.getenv(
        'RATELIMIT_STORAGE_URL',
        'memory://'
    )

    # CORS
    _DEFAULT_CORS_ORIGINS = (
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5500',
        'http://127.0.0.1:5500',
    )

    _ENV_CORS_ORIGINS = tuple(
        origin.strip().rstrip('/')
        for origin in os.getenv('CORS_ORIGINS', '').split(',')
        if origin.strip()
    )

    CORS_ORIGINS = list(
        dict.fromkeys(_DEFAULT_CORS_ORIGINS + _ENV_CORS_ORIGINS)
    )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}