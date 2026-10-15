from rest_framework.throttling import AnonRateThrottle


class AdminRequestThrottle(AnonRateThrottle):
    rate = "10/min"

class UserRequestThrottle(AnonRateThrottle):
    rate = "6/min"
