"""
Base configuration for the Django project.

In this module, the basic settings of the application are defined. Basic settings include the application language,
application time, request type, application main path, and other related settings.
"""

from pathlib import Path

from config.settings.env import env

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPLICATION_DOMAIN = env.str("APPLICATION_DOMAIN")
