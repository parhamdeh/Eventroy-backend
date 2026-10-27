from django.conf import settings
from rest_framework import serializers


class WalletChargeInputSerializer(serializers.Serializer):
    amount = serializers.IntegerField(
        min_value=settings.PAYMENT_MIN_AMOUNT,
        max_value=settings.PAYMENT_MAX_AMOUNT,
        help_text="Amount in tomans.",
    )


class WalletChargeOutputSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    authority = serializers.CharField()
    payment_url = serializers.URLField()


class VerifyQuerySerializer(serializers.Serializer):
    Authority = serializers.CharField(max_length=100)
    Status = serializers.ChoiceField(choices=["OK", "NOK"])