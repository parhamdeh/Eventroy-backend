from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class PaymentCreateThrottle(UserRateThrottle):
    """
    Limit how often one authenticated user can start a payment.

    Keyed by user id. The rate lives on the class, so nothing needs to be
    added to REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
    """

    scope = "payment_create"
    rate = "10/hour"


class PaymentCallbackThrottle(AnonRateThrottle):
    """
    Limit hits on the gateway callback, keyed by client IP.

    The callback has no authentication, so every request is anonymous.
    Behind nginx / a load balancer set REST_FRAMEWORK["NUM_PROXIES"]
    correctly, otherwise all users share the proxy's IP and one bucket.
    """

    scope = "payment_callback"
    rate = "60/minute"