from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Host

class APIKeyAuthentication(BaseAuthentication):
    """
    Custom API key authentication for agents.
    Only applies if 'X-API-KEY' header is present.
    """
    def authenticate(self, request):
        key = request.headers.get('X-API-KEY')
        if not key:
            return None  # Skip → AllowAny or other permission classes decide

        try:
            host = Host.objects.get(api_key=key)
        except Host.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

        # Return (user, auth) → DRF will treat Host as the "user"
        return (host, None)
