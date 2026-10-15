from django.utils.translation import gettext_lazy as _
from rest_framework import status


class ApplicationError(Exception):
    """Base error for all domain and API failures."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "error"
    default_message = _("An error occurred.")

    def __init__(self, message=None, *, code=None, extra=None, status_code=None):
        self.message = message if message is not None else self.default_message
        self.code = code or self.default_code
        self.extra = extra or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(str(self.message))


class BadRequestError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bad_request"
    default_message = _("Bad request.")


class ValidationFailedError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"
    default_message = _("Validation error.")


class UnauthorizedError(ApplicationError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "authentication_required"
    default_message = _("Authentication required.")


class InvalidCredentialsError(UnauthorizedError):
    default_code = "invalid_credentials"
    default_message = _("Invalid credentials.")


class TokenInvalidError(UnauthorizedError):
    default_code = "token_invalid"
    default_message = _("Invalid token.")


class TokenExpiredError(UnauthorizedError):
    default_code = "token_expired"
    default_message = _("Token has expired.")


class ForbiddenError(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "permission_denied"
    default_message = _("You do not have permission to perform this action.")


class AccountDisabledError(ForbiddenError):
    default_code = "account_disabled"
    default_message = _("Account is disabled.")


class AccountNotVerifiedError(ForbiddenError):
    default_code = "account_not_verified"
    default_message = _("Account is not verified.")


class NotFoundError(ApplicationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
    default_message = _("Not found.")


class MethodNotAllowedError(ApplicationError):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_code = "method_not_allowed"
    default_message = _("Method not allowed.")


class ConflictError(ApplicationError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_message = _("Resource already exists.")


class AlreadyExistsError(ConflictError):
    default_code = "already_exists"
    default_message = _("Resource already exists.")


class GoneError(ApplicationError):
    status_code = status.HTTP_410_GONE
    default_code = "gone"
    default_message = _("This resource is no longer available.")


class PayloadTooLargeError(ApplicationError):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_code = "payload_too_large"
    default_message = _("Request payload is too large.")


class UnsupportedMediaTypeError(ApplicationError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_code = "unsupported_media_type"
    default_message = _("Unsupported media type.")


class UnprocessableEntityError(ApplicationError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "unprocessable_entity"
    default_message = _("Unprocessable entity.")


class TooManyRequestsError(ApplicationError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "too_many_requests"
    default_message = _("Too many requests. Please try again later.")


class InternalServerError(ApplicationError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = "internal_error"
    default_message = _("Internal server error.")


class ServiceUnavailableError(ApplicationError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "service_unavailable"
    default_message = _("Service unavailable.")
