from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler

from app.core.exceptions import ApplicationError

_DRF_ERROR_MAP = {
    "not_authenticated": ("authentication_required", _lazy("Authentication required.")),
    "authentication_failed": ("invalid_credentials", _lazy("Invalid credentials.")),
    "permission_denied": (
        "permission_denied",
        _lazy("You do not have permission to perform this action."),
    ),
    "not_found": ("not_found", _lazy("Not found.")),
    "method_not_allowed": ("method_not_allowed", _lazy("Method not allowed.")),
    "unsupported_media_type": ("unsupported_media_type", _lazy("Unsupported media type.")),
    "throttled": ("too_many_requests", _lazy("Too many requests. Please try again later.")),
    "parse_error": ("bad_request", _lazy("Bad request.")),
}


def _payload(*, message, error_code, errors=None):
    return {
        "message": str(message),
        "error_code": error_code,
        "errors": errors or {},
    }


def _response(message, error_code, http_status, errors=None):
    return Response(
        _payload(message=message, error_code=error_code, errors=errors),
        status=http_status,
    )


def _field_errors(detail):
    if isinstance(detail, dict):
        return detail
    if isinstance(detail, list):
        return {"non_field_errors": detail}
    return {"non_field_errors": [detail]}


def custom_exception_handler(exc, ctx):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, ApplicationError):
        return _response(
            exc.message,
            exc.code,
            exc.status_code,
            errors=exc.extra or None,
        )

    if isinstance(exc, IntegrityError):
        return _response(
            _("Resource already exists."),
            "already_exists",
            status.HTTP_409_CONFLICT,
        )

    response = exception_handler(exc, ctx)

    if response is None:
        if settings.DEBUG:
            return None
        return _response(
            _("A server error occurred."),
            "internal_error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, exceptions.ValidationError):
        return _response(
            _("Validation error."),
            "validation_error",
            response.status_code,
            errors=_field_errors(response.data),
        )

    drf_code = getattr(exc, "default_code", None) or getattr(exc, "code", None)
    mapped = _DRF_ERROR_MAP.get(drf_code)
    if mapped:
        error_code, default_message = mapped
        detail = response.data.get("detail", default_message) if isinstance(response.data, dict) else default_message
        return _response(detail, error_code, response.status_code)

    if isinstance(response.data, dict) and "detail" in response.data:
        return _response(response.data["detail"], drf_code or "error", response.status_code)

    return _response(
        _("An error occurred."),
        drf_code or "error",
        response.status_code,
        errors=_field_errors(response.data),
    )
