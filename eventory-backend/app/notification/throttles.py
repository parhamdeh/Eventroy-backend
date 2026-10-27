from rest_framework.throttling import UserRateThrottle


class WsTicketThrottle(UserRateThrottle):
    scope = "ws_ticket"
    rate = "30/minute"