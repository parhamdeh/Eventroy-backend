
LOCAL_APPS = [
    "app.core.apps.CoreConfig",
    "app.common.apps.CommonConfig",
    "app.users.apps.UsersConfig",
    "app.sms_gateway.apps.SmsGatewayConfig",
    "app.event.apps.EventConfig",
    "app.payment_gateway.apps.PaymentGatewayConfig",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "django_celery_results",
    "django_celery_beat",
    "corsheaders",
    "drf_spectacular",
    "django_extensions",
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    *THIRD_PARTY_APPS,
    *LOCAL_APPS,
]

