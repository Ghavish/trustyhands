"""
Django settings for the TrustyHands project.

Secrets and the MongoDB Atlas connection string are read from the ".env"
file in the project root. Never write them directly in this file.
"""

import os
from pathlib import Path

import certifi
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

# --- Paths and environment ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# --- Applications ---
INSTALLED_APPS = [
    # Django contrib apps, adapted for MongoDB ids (see trustyhands/apps.py)
    "trustyhands.apps.MongoAdminConfig",
    "trustyhands.apps.MongoAuthConfig",
    "trustyhands.apps.MongoContentTypesConfig",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_mongodb_backend",

    # TrustyHands core base
    "users",
    "core",

    # TrustyHands role views
    "client",
    "service_provider",
    "platform_admin",
]

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ["users.backends.EmailOrPhoneBackend"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.UserPreferencesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trustyhands.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "trustyhands.wsgi.application"


# --- Database: MongoDB Atlas ---
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": MONGODB_URI,
        "NAME": os.getenv("MONGODB_NAME", "trustyhands"),
        # Atlas uses TLS. certifi gives every laptop the same trusted
        # certificates, which avoids "certificate verify failed" errors.
        "OPTIONS": (
            {"tlsCAFile": certifi.where()}
            if MONGODB_URI.startswith("mongodb+srv") else {}
        ),
    },
}

# MongoDB uses ObjectId primary keys instead of numbers.
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"

# Django's own apps get MongoDB-friendly migrations from this folder.
MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}


# --- Passwords (FR 1.6: minimum strength) ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation."
             "UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "core:after_login"
LOGOUT_REDIRECT_URL = "core:home"


# --- Languages: English and French (FR 9.1) ---
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True

TIME_ZONE = "Indian/Mauritius"
USE_TZ = True


# --- Static files and uploads ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Allow up to 10 photos of 5 MB each in one booking form.
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024


# --- Email: printed in the terminal while developing ---
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
DEFAULT_FROM_EMAIL = "TrustyHands <no-reply@trusty-hands.mu>"


# --- Cookie that remembers a guest's theme choice ---
THEME_COOKIE_NAME = "th_theme"
