from django.db import models


class NotificationKind(models.TextChoices):
    SYSTEM = "SYSTEM", "System"
    WALLET_CHARGED = "WALLET_CHARGED", "Wallet charged"
    # add more kinds here (ORDER_PAID, EVENT_APPROVED, ...)