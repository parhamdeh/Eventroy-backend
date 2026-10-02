import datetime

from config.env import env

# Docs: https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html

ACCESS_TOKEN_LIFETIME_SECONDS = env("ACCESS_TOKEN_LIFETIME_SECONDS", default=60 * 5)  # 5 minutes
REFRESH_TOKEN_LIFETIME_SECONDS = env("REFRESH_TOKEN_LIFETIME_SECONDS", default=60 * 60 * 24 * 7)  # 7 days

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(seconds=ACCESS_TOKEN_LIFETIME_SECONDS),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(seconds=REFRESH_TOKEN_LIFETIME_SECONDS),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,

    "AUTH_HEADER_TYPES": ("Bearer",),

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
# AUTH_USER_MODEL = 'users.BaseUser'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"