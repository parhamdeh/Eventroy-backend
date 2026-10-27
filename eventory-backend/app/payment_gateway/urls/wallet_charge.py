from django.urls import path

from app.payment_gateway.api import WalletChargeCreateAPI

urlpatterns = [
    path(
        "wallet-charge/",
        WalletChargeCreateAPI.as_view(),
        name="wallet-charge",
    ),
]