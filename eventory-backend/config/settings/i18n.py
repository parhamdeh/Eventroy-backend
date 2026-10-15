
import os

from django.utils.translation import gettext_lazy as _

from config.settings.base import BASE_DIR
from config.settings.env import env

LOCALE_PATHS = [os.path.join(BASE_DIR, "app/locale")]

LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en")
LANGUAGES = [
    ("en", _("English")),
    ("fa", _("Persian")),
    ("ar", _("Arabic")),
]

TIME_ZONE = env.str("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True
