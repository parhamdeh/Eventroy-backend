# Third Party Packages
from rest_framework.renderers import JSONRenderer
 

class CustomResponseRenderer(JSONRenderer):
    """
    Wraps every API response in a consistent envelope:

        {
            "data": <original response payload, or null on error>,
            "msg": <human-readable message>,
            "code": <HTTP status code>
        }
    """

    default_success_message = "Success"
    default_error_message = "Error"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = response.status_code if response is not None else 200

        is_error = status_code >= 400

        msg = self.default_error_message if is_error else self.default_success_message
        payload = data

        if is_error and isinstance(data, dict):
            if "detail" in data:
                msg = str(data["detail"])
                payload = None
            else:
                first_key = next(iter(data), None)
                if first_key is not None:
                    first_val = data[first_key]
                    msg = first_val[0] if isinstance(first_val, list) else str(first_val)
                payload = data

        wrapped = {
            "data": None if is_error and payload is None else payload,
            "msg": msg,
            "code": status_code,
        }

        return super().render(wrapped, accepted_media_type, renderer_context)