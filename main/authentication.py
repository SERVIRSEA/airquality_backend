from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey  # Import your APIKey model

class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get('HTTP_AUTHORIZATION')  # Get the API key from the request headers
        if api_key:
            try:
                # Look up the API key in the database
                api_key_object = APIKey.objects.get(key=api_key)

                # Return a tuple of (user, auth) where 'user' is the user associated with the API key (or None)
                # and 'auth' is the API key object itself
                return (api_key_object.user, api_key_object)

            except APIKey.DoesNotExist:
                raise AuthenticationFailed('Invalid API key')
        return None