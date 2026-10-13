from config.env import env

DEFAULT_PROTOCOL = "http"

SANDBOX = True
MERCHANT = env("MERCHANT")
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"

CALLBACK_URL = "http://127.0.0.1:8000/api/subscriptions/verify/"