from rest_framework.response import Response
from rest_framework import status


def plum_error_response(
    *,
    field: str,
    uz: str,
    ru: str,
    en: str,
):
    return Response(
        {
            "success": False,
            "code": -999,
            "data": {
                "amount": [
                    en,
                ],
            },
            "message": "Error",
            "client_message": {
                "uz": uz,
                "ru": ru,
                "en": en,
            },
        },
        status=status.HTTP_200_OK,
    )