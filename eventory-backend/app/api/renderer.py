from django.utils.translation import gettext as _
from rest_framework.renderers import JSONRenderer


class CustomResponseRenderer(JSONRenderer):
    """
    Wraps every API response in a consistent envelope:

        {
            "data": <payload or null on error>,
            "msg": <human-readable message>,
            "code": <HTTP status code>,
            "error_code": <machine-readable code or null>,
            "errors": <field errors or null>
        }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = response.status_code if response is not None else 200
        is_error = status_code >= 400

        error_code = None
        errors = None
        payload = data
        msg = _("Error") if is_error else _("Success")

        if isinstance(data, dict):
            if is_error:
                msg = data.get("message") or data.get("msg") or data.get("detail") or msg
                if isinstance(msg, list):
                    msg = msg[0]
                error_code = data.get("error_code")
                errors = data.get("errors") or None
                payload = None
            elif "data" in data and {"msg", "code"} <= data.keys():
                return super().render(data, accepted_media_type, renderer_context)

        wrapped = {
            "data": payload,
            "msg": str(msg),
            "code": status_code,
            "error_code": error_code,
            "errors": errors,
        }

        return super().render(wrapped, accepted_media_type, renderer_context)
