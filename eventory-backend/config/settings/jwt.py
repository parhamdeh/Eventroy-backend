import datetime

from config.env import env

# Docs: https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html

ACCESS_TOKEN_LIFETIME_SECONDS = env.int("ACCESS_TOKEN_LIFETIME_SECONDS", default=60 * 5)
REFRESH_TOKEN_LIFETIME_SECONDS = env.int("REFRESH_TOKEN_LIFETIME_SECONDS", default=60 * 60 * 24 * 7)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(seconds=ACCESS_TOKEN_LIFETIME_SECONDS),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(seconds=REFRESH_TOKEN_LIFETIME_SECONDS),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"