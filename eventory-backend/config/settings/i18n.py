
import os

from config.settings.base import BASE_DIR
from config.settings.env import env

LOCALE_PATHS = [os.path.join(BASE_DIR, "app/locale")]

LANGUAGE_CODE = env.str("LANGUAGE_CODE")
LANGUAGES = [("en", "English"), ("fa", "Persian")]

TIME_ZONE = env.str("TIME_ZONE")
USE_I18N = True
USE_TZ = True
