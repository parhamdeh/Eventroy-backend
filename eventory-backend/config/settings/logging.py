from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
os.makedirs(BASE_DIR / "logs", exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {module}:{lineno} - {message}",
            "style": "{",
        },
    },

    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "when": "midnight",      
            "interval": 1,           
            "backupCount": 30,       
            "encoding": "utf-8",
            "formatter": "verbose",
        },

        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

