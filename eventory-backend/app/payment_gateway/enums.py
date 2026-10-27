from django.db import models


class PaymentPurpose(models.TextChoices):
    WALLET_CHARGE = "WALLET_CHARGE", "Wallet Charge"
    # ORDER = "ORDER", "Order"   # add when orders go through the gateway


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELED = "CANCELED", "Canceled"
    EXPIRED = "EXPIRED", "Expired"


class PaymentGatewayName(models.TextChoices):
    ZARINPAL = "zarinpal", "ZarinPal"