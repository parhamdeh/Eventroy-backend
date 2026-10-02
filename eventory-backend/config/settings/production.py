from . import *  # noqa
from config.env import env

DEBUG = False

SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)

# https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/5.2/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/5.2/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "SECURE_CONTENT_TYPE_NOSNIFF", default=True
)