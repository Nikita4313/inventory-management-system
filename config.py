"""
Flask application configuration
"""
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base configuration"""
    SECRET_KEY = config('SECRET_KEY', default='flask-inventory-secret-key-change-in-production-2024')
    DEBUG = config('DEBUG', default=True, cast=bool)
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = config(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "inventory.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # WTForms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
