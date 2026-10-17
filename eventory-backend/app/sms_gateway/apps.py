from django.apps import AppConfig


class SmsGatewayConfig(AppConfig):
    """Django app config for the reusable messaging gateway."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.sms_gateway"
    verbose_name = "SMS Gateway"
