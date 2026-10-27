from .verify import urlpatterns as payment_verify_urlpatterns
from .wallet_charge import urlpatterns as wallet_charge_urlpatterns

app_name = "payments"

urlpatterns = [
    *wallet_charge_urlpatterns,
    *payment_verify_urlpatterns,
]