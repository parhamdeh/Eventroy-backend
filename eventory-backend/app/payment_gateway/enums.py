
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentType(models.TextChoices):
    """Supported payment purposes."""

    ORDER = "ORDER", _("Order")
    WALLET_CHARGE = "WALLET_CHARGE", _("Wallet charge")


class PaymentStatus(models.TextChoices):
    """Possible payment lifecycle statuses."""

    PENDING = "PENDING", _("Pending")
    SUCCESS = "SUCCESS", _("Success")
    FAILED = "FAILED", _("Failed")
    CANCELED = "CANCELED", _("Canceled")


class EntryType(models.TextChoices):
    """Financial entry categories associated with a transaction."""

    PRINCIPAL = "PRINCIPAL", _("Principal")
    COMMISSION = "COMMISSION", _("Commission")


class GatewayType(models.TextChoices):
    """Supported payment gateways."""

    ZARINPAL = "zarinpal", _("ZarinPal")
