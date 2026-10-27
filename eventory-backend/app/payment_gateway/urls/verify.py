from django.urls import path

from app.payment_gateway.api.charge_api import PaymentVerifyAPI

urlpatterns = [
    path(
        "verify/",
        PaymentVerifyAPI.as_view(),
        name="verify",
    ),
]