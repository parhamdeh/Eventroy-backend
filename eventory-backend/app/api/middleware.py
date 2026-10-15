# Third Party Packages
import time
import logging

# Django Built-in modules
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)



class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration = (time.perf_counter() - start_time) * 1000

        if request.user.is_authenticated:
            user = request.user.username
        else:
            user = "Anonymous"

        ip = request.META.get("REMOTE_ADDR")

        user_agent = request.META.get("HTTP_USER_AGENT", "-")

        logger.info(
            f"[{request.method}] {request.path} | "
            f"User={user} | "
            f"IP={ip} | "
            f"Status={response.status_code} | "
            f"{duration:.2f} ms | "
            f"{user_agent}"
        )
        return response