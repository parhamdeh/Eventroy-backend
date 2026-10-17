from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AdminRequestThrottle(UserRateThrottle):
    """Throttle for authenticated administrator endpoints."""

    scope = "admin"


class UserRequestThrottle(UserRateThrottle):
    """Throttle for authenticated user endpoints."""

    scope = "user"


class AuthRateThrottle(AnonRateThrottle):
    """IP-based throttle for login and token refresh."""

    scope = "auth"


class OTPRequestThrottle(AnonRateThrottle):
    """IP-based throttle for OTP issuance endpoints."""

    scope = "otp"
