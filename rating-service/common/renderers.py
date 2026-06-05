from rest_framework.renderers import JSONRenderer


class APIJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        status_code = response.status_code if response else 200

        if data is not None and "success" not in data:
            if status_code >= 400:
                wrapped = {"success": False, "message": data.get("detail", str(data)) if isinstance(data, dict) else str(data)}
                if isinstance(data, dict):
                    wrapped["errors"] = {k: v for k, v in data.items() if k != "detail"}
                data = wrapped
            else:
                data = {"success": True, "message": "Success", "data": data}

        return super().render(data, accepted_media_type, renderer_context)
