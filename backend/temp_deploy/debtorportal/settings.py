"""
Django settings for debtorportal project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allowed hosts - comma-separated list in env, or allow all in debug mode
_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',')]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'debtorportal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'debtorportal.wsgi.application'

# Database - Using SQLite for Django admin, MongoDB for app data
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MongoDB Settings
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_NAME = os.getenv('MONGODB_NAME', 'debtor_portal')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
# Allow all origins for now (API is protected by JWT)
# In production with specific domains, use CORS_ALLOWED_ORIGINS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Disable browsable API in production (requires django.test which is stripped in Lambda)
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# File Upload Settings (for bulk PDF processing)
DATA_UPLOAD_MAX_NUMBER_FILES = 50000  # Allow up to 50,000 files per request
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB max request size
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB per file

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Email Settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@debtorportal.com')

# Collections team email - where payment interest notifications will be sent
COLLECTIONS_TEAM_EMAIL = os.getenv('COLLECTIONS_TEAM_EMAIL', 'collections@example.com')

# ============================================
# AWS SERVERLESS CONFIGURATION
# ============================================

# AWS Region
AWS_REGION = os.getenv('AWS_REGION', os.getenv('S3_REGION', 'ap-southeast-1'))

# S3 Storage Configuration
USE_S3_STORAGE = os.getenv('USE_S3_STORAGE', 'False').lower() == 'true'
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', os.getenv('AWS_STORAGE_BUCKET_NAME', ''))
S3_REGION = os.getenv('S3_REGION', AWS_REGION)

# For django-storages compatibility (optional)
if USE_S3_STORAGE and S3_BUCKET_NAME:
    AWS_STORAGE_BUCKET_NAME = S3_BUCKET_NAME
    AWS_S3_REGION_NAME = S3_REGION
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None  # Use bucket default ACL
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 day cache
    }

# SQS Configuration (for PDF processing)
PDF_QUEUE_URL = os.getenv('PDF_QUEUE_URL', '')
USE_SQS_FOR_PDF = os.getenv('USE_SQS_FOR_PDF', 'False').lower() == 'true' or bool(PDF_QUEUE_URL)

# AWS SES Email Configuration
USE_SES_EMAIL = os.getenv('USE_SES_EMAIL', 'False').lower() == 'true'
SES_SENDER_EMAIL = os.getenv('SES_SENDER_EMAIL', DEFAULT_FROM_EMAIL)

if USE_SES_EMAIL:
    # Override email backend to use SES
    EMAIL_BACKEND = 'api.aws_email.SESEmailBackend'

# Lambda/Serverless specific settings
IS_LAMBDA = os.getenv('AWS_LAMBDA_FUNCTION_NAME', '') != ''
if IS_LAMBDA:
    # Disable CSRF for Lambda (API Gateway handles this)
    CSRF_TRUSTED_ORIGINS = ['*']
    # Allow all hosts for Lambda (API Gateway restricts access)
    ALLOWED_HOSTS = ['*']
    # Disable debug in Lambda
    DEBUG = False
    # Use /tmp for any temporary files in Lambda
    TEMP_DIR = '/tmp'
else:
    TEMP_DIR = os.getenv('TEMP_DIR', str(BASE_DIR / 'tmp'))

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'media'

# Static files for Lambda
if IS_LAMBDA:
    STATIC_ROOT = '/tmp/static'
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Logging configuration for Lambda
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if IS_LAMBDA else 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if IS_LAMBDA else 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
