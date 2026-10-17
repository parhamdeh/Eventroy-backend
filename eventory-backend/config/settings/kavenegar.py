from config.env import env


KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY", default="")
KAVENEGAR_SENDER = env("SENDER", default="")
SMS_PROVIDER = env("SMS_PROVIDER", default="kavenegar")



