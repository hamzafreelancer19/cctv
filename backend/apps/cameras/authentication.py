from django.conf import settings
from rest_framework import authentication, exceptions

from .models import EdgeDevice


class EdgeAPIKeyAuthentication(authentication.BaseAuthentication):
    header_name = "X-Edge-API-Key"

    def authenticate(self, request):
        api_key = request.headers.get(self.header_name) or request.headers.get("Authorization", "").removeprefix("Edge ")
        if not api_key:
            return None

        key_hash = EdgeDevice.hash_api_key(api_key)
        try:
            device = EdgeDevice.objects.select_related("site__organization").get(
                api_key_hash=key_hash, is_active=True
            )
        except EdgeDevice.DoesNotExist:
            if api_key == settings.EDGE_API_KEY:
                return (EdgeServiceUser(), None)
            raise exceptions.AuthenticationFailed("Invalid edge API key.")

        request.edge_device = device
        return (EdgeServiceUser(device=device), None)


class EdgeServiceUser:
    is_authenticated = True
    is_active = True
    is_staff = False
    is_superuser = False

    def __init__(self, device=None):
        self.device = device
        self.username = "edge-service"
        self.pk = device.id if device else None

    @property
    def organization(self):
        if self.device:
            return self.device.site.organization
        return None
