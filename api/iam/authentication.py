from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from jwt import PyJWKClient
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings


class ServiceUser:
    """Lightweight user wrapper representing the authenticated token payload."""

    def __init__(self, payload):
        self.payload = payload
        self.is_authenticated = True
        self.id = payload.get("userId")
        self.aud = payload.get("aud")
        self.scopes = payload.get("scope", [])

    def has_scope(self, required_scope: str) -> bool:
        return required_scope in self.scopes or f"{self.aud}:*" in self.scopes


class JWKSAuthentication(BaseAuthentication):
    """
    DRF Authentication Class using remote JWKS endpoint from the Auth service.
    """

    def __init__(self):
        self.jwks_client = PyJWKClient(settings.AUTH_JWKS_URL)

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None

        return self._authenticate_token(token, raise_on_error=True), token

    def authenticate_token(self, token: str):
        """
        Validate a raw JWT outside of DRF requests (e.g., WebSocket connections).
        Returns a ServiceUser on success, or None when invalid or expired.
        """
        return self._authenticate_token(token, raise_on_error=False)

    def _authenticate_token(self, token: str, raise_on_error: bool):
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=api_settings.ALGORITHM,
                audience=settings.CLIENT_ID,
            )
            return ServiceUser(payload)
        except jwt.ExpiredSignatureError:
            if raise_on_error:
                raise AuthenticationFailed("Token has expired.")
            return None
        except jwt.InvalidAudienceError:
            if raise_on_error:
                raise AuthenticationFailed("Token audience does not match this service.")
            return None
        except jwt.PyJWTError as e:
            if raise_on_error:
                raise AuthenticationFailed(f"Invalid token: {str(e)}")
            return None


class JWTAuthMiddleware:
    """
    WebSocket middleware that extracts the token from cookies and delegates
    verification to JWKSAuthentication.authenticate(). Falls back to AnonymousUser
    without rejecting connections.
    """
    def __init__(self, inner):
        # Store the next ASGI application in the stack.
        self.inner = inner
        self.jwks_auth = JWKSAuthentication()

    async def __call__(self, scope, receive, send):
        # Resolve the user only for WebSocket connections.
        if scope["type"] == "websocket":
            scope["user"] = await self.get_user_from_scope(scope)
        return await self.inner(scope, receive, send)

    def _get_token_from_query(self, scope):
        # Parse the raw query string from ASGI scope (bytes) and read `token`.
        raw_query = scope.get("query_string") or b""
        query_params = parse_qs(raw_query.decode("utf-8", errors="ignore"))
        token_list = query_params.get("token")
        if not token_list:
            return None

        token = token_list[0].strip()
        return token or None

    @database_sync_to_async
    def get_user_from_scope(self, scope):
        token = self._get_token_from_query(scope)
        auth_header = f"Bearer {token}" if token else None

        # Build a lightweight request-like object so JWKSAuthentication.authenticate() can be reused.
        request_stub = type("RequestStub", (), {"headers": {"Authorization": auth_header}})()

        try:
            auth_result = self.jwks_auth.authenticate(request_stub)
            if auth_result:
                user, _ = auth_result
                return user
            return AnonymousUser()
        except AuthenticationFailed:
            # Leave permission checks to the consumer rather than rejecting at the middleware layer.
            return AnonymousUser()
