import base64
import binascii
import secrets

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class PlumWebhookUser:
    is_authenticated = True


class PlumBasicAuthentication(BaseAuthentication):

    def authenticate(self, request):
        authorization = request.headers.get("Authorization")

        if not authorization:
            raise AuthenticationFailed(
                "Authorization header is required."
            )

        try:
            scheme, credentials = authorization.split(" ", 1)
        except ValueError:
            raise AuthenticationFailed(
                "Invalid Authorization header."
            )

        if scheme.lower() != "basic":
            raise AuthenticationFailed(
                "Basic Authentication is required."
            )

        try:
            decoded = base64.b64decode(
                credentials
            ).decode("utf-8")

            username, password = decoded.split(":", 1)

        except (
            ValueError,
            UnicodeDecodeError,
            binascii.Error,
        ):
            raise AuthenticationFailed(
                "Invalid Basic Authentication credentials."
            )

        valid_username = settings.PLUM_WEBHOOK_USERNAME
        valid_password = settings.PLUM_WEBHOOK_PASSWORD

        username_valid = secrets.compare_digest(
            username,
            valid_username,
        )

        password_valid = secrets.compare_digest(
            password,
            valid_password,
        )

        if not username_valid or not password_valid:
            raise AuthenticationFailed(
                "Invalid username or password."
            )

        return (
            PlumWebhookUser(),
            None,
        )

    def authenticate_header(self, request):
        return "Basic realm=\"Plum Webhook\""