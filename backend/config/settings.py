"""
Django settings for USERinator project.

USERinator is the user & company management microservice for the Inator Platform.
Follows INATOR.md standards for non-Authinator services.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config(
    "SECRET_KEY", default="django-insecure-dev-key-change-in-production"
)
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# External domain deployment support
DEPLOY_DOMAIN = config("DEPLOY_DOMAIN", default="")
DEPLOY_SCHEME = config("DEPLOY_SCHEME", default="https" if DEPLOY_DOMAIN else "http")

if DEPLOY_DOMAIN:
    # Add deployment domain and bare variant to ALLOWED_HOSTS
    ALLOWED_HOSTS.append(DEPLOY_DOMAIN)
    bare_domain = DEPLOY_DOMAIN.replace("www.", "")
    if bare_domain != DEPLOY_DOMAIN:
        ALLOWED_HOSTS.append(bare_domain)


# Application definition

INSTALLED_APPS = [
    # Admin interface (must be before django.contrib.admin)
    "admin_interface",
    "colorfield",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "core",
    "users",
    "companies",
    "roles",
    "invitations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # MUST be early
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database (SQLite for development per INATOR.md 2.2.9)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model for database relations only
# NOTE: Authentication is handled by Authinator, not this model
AUTH_USER_MODEL = "users.User"

# Authinator configuration
AUTHINATOR_API_URL = config(
    "AUTHINATOR_API_URL", default="http://localhost:8001/api/auth/"
)
AUTHINATOR_VERIFY_SSL = config("AUTHINATOR_VERIFY_SSL", default=False, cast=bool)

# Service Registry configuration
SERVICE_REGISTRY_URL = config(
    "SERVICE_REGISTRY_URL",
    default="http://localhost:8001/api/services/register/",
)
SERVICE_REGISTRATION_KEY = config(
    "SERVICE_REGISTRATION_KEY",
    default="dev-service-key-change-in-production",
)

# Internal service-to-service authentication key
# Other Inator services use this to call USERinator endpoints directly
INTERNAL_SERVICE_KEY = config(
    "INTERNAL_SERVICE_KEY",
    default="dev-internal-service-key-change-in-production",
)

# REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.AuthinatorJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Simple JWT configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS configuration — all traffic flows through the Caddy gateway (:8080)
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:8080",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# Add deployment domain to CORS if configured
if DEPLOY_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"{DEPLOY_SCHEME}://{DEPLOY_DOMAIN}")
    bare_domain = DEPLOY_DOMAIN.replace("www.", "")
    if bare_domain != DEPLOY_DOMAIN:
        CORS_ALLOWED_ORIGINS.append(f"{DEPLOY_SCHEME}://{bare_domain}")

CORS_ALLOW_CREDENTIALS = True

# Session cookie settings
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = bool(DEPLOY_DOMAIN and DEPLOY_SCHEME == "https")
SESSION_COOKIE_HTTPONLY = True

# CSRF configuration
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = bool(DEPLOY_DOMAIN and DEPLOY_SCHEME == "https")
CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

# Add deployment domain to CSRF trusted origins
if DEPLOY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"{DEPLOY_SCHEME}://{DEPLOY_DOMAIN}")
    bare_domain = DEPLOY_DOMAIN.replace("www.", "")
    if bare_domain != DEPLOY_DOMAIN:
        CSRF_TRUSTED_ORIGINS.append(f"{DEPLOY_SCHEME}://{bare_domain}")

# Email configuration (console backend for development)
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@userinator.local")

# Admin interface settings
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]  # X-Frame-Options warning

# Django sites framework
SITE_ID = 1

# Authentication handled by Authinator external service
# No local authentication backends needed
