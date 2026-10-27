from config.env import env

DEFAULT_PROTOCOL = "http"

PAYMENT_DEFAULT_GATEWAY = "zarinpal"
PAYMENT_MIN_AMOUNT = 10_000          # tomans
PAYMENT_MAX_AMOUNT = 50_000_000      # tomans
PAYMENT_PENDING_TTL_MINUTES = 60

SANDBOX = True
ZARINPAL_MERCHANT_ID = env("MERCHANT", default="")
ZARINPAL_TIMEOUT = 10
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"

CALLBACK_URL = "http://127.0.0.1:8000/api/subscriptions/verify/"