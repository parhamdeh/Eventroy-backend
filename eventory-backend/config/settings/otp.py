"""Cache-backed OTP configuration. Values come from the environment."""

from config.settings.env import env

OTP_TTL_SECONDS = env.int("OTP_TTL_SECONDS", default=300)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)
OTP_RESEND_COOLDOWN_SECONDS = env.int("OTP_RESEND_COOLDOWN_SECONDS", default=60)
OTP_DELIVERY_TTL_SECONDS = env.int("OTP_DELIVERY_TTL_SECONDS", default=60)
OTP_LENGTH = 6
OTP_CACHE_PREFIX = env("OTP_CACHE_PREFIX", default="eventory:otp")
