from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import Host

class ApiKeyAuthentication(BaseAuthentication):
    header = 'X-API-Key'

    def authenticate(self, request):
        api_key = request.headers.get(self.header)
        if not api_key:
            raise exceptions.AuthenticationFailed('Missing API key')
        try:
            host = Host.objects.get(api_key=api_key)
        except Host.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        host.is_authenticated = True
        return (host, None)