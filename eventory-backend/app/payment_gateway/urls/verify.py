from django.urls import path

from app.payment_gateway.api import PaymentVerifyAPI

urlpatterns = [
    path(
        "verify/",
        PaymentVerifyAPI.as_view(),
        name="verify",
    ),
]