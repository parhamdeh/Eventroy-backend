"""Isolated Django settings for the pytest suite."""

from config.settings import *  # noqa: F403

DEBUG = True

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "eventory-tests",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

KAVENEGAR_API_KEY = "test-kavenegar-key"
KAVENEGAR_SENDER = "1000"
SMS_PROVIDER = "kavenegar"

GOOGLE_CLIENT_ID = "test-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "test-google-client-secret"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "test-media"  # noqa: F405

OTP_TTL_SECONDS = 120
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 30
OTP_DELIVERY_TTL_SECONDS = 60
