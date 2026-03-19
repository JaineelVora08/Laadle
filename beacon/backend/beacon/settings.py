"""
Django settings for beacon project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'changeme')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '*').split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    # Local apps
    'apps.auth_service',
    'apps.user_profile_service',
    'apps.domain_management_service',
    'apps.mentor_matching_service',
    'apps.trust_score_service',
    'apps.query_orchestrator',
    'apps.ai_services',
    'apps.adaptive_scheduler_service',
    'apps.direct_messaging_service',
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

ROOT_URLCONF = 'beacon.urls'

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

WSGI_APPLICATION = 'beacon.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
    # Production (PostgreSQL):
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': os.getenv('POSTGRES_DB', 'beacon_db'),
    #     'USER': os.getenv('POSTGRES_USER', 'beacon_user'),
    #     'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'beacon_pass'),
    #     'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
    #     'PORT': os.getenv('POSTGRES_PORT', '5432'),
    # }
}

AUTH_USER_MODEL = 'auth_service.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Neo4j Aura — neomodel requires bolt+s:// with credentials embedded in the URL
_neo4j_host = os.getenv('NEO4J_HOST', '269dc5fe.databases.neo4j.io')
_neo4j_user = os.getenv('NEO4J_USERNAME', '269dc5fe')
_neo4j_pass = os.getenv('NEO4J_PASSWORD', '')
NEOMODEL_NEO4J_BOLT_URL = f'neo4j+s://{_neo4j_user}:{_neo4j_pass}@{_neo4j_host}'

# Explicitly set neomodel's connection URL (it doesn't auto-read Django settings)
from neomodel import config as _neomodel_config
_neomodel_config.DATABASE_URL = NEOMODEL_NEO4J_BOLT_URL
_neomodel_config.DATABASE_NAME = os.getenv('NEO4J_DATABASE', '269dc5fe')

# Pinecone
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY', 'pcsk_3YD3KU_8embZDpEKdCUiLdPXNspijX5r5gGXVsagT3jBJo8xRjNgUM8j9pAUMZ9mKuMyJV')
PINECONE_ENV = os.getenv('PINECONE_ENV', 'us-east-1-aws')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'beacon-domains')

# Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Internal Service Auth
INTERNAL_SECRET = os.getenv('INTERNAL_SECRET', 'internal_shared_secret')
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '735972244009-9l7etrnnfi44pk37jaevdl393ckaf1d9.apps.googleusercontent.com')
VITE_GOOGLE_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '735972244009-9l7etrnnfi44pk37jaevdl393ckaf1d9.apps.googleusercontent.com')

GOOGLE_OAUTH_CLIENT_IDS = [
    client_id.strip()
    for client_id in os.getenv('GOOGLE_OAUTH_CLIENT_IDS', GOOGLE_OAUTH_CLIENT_ID).split(',')
    if client_id.strip()
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
