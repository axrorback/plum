from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from .services import PlumWebhookService , PlumPaymentService
from django.db import transaction
from .models import Order , OrderStatus
from .auth import PlumBasicAuthentication
from rest_framework.permissions import IsAuthenticated



class CreateOrderAPIView(APIView):

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        user = request.user

        order = Order.objects.create(
            account=data["account"],
            amount=data["amount"],
            purpose=data["purpose"],
            user_full_name=user.get_full_name(),
            return_url=data.get("return_url", ""),
            callback_url=data.get("callback_url", ""),
        )

        try:
            invoice = PlumPaymentService.create_invoice(
                order=order,
            )

        except Exception as exc:
            order.status = OrderStatus.FAILED

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "success": False,
                    "message": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        checkout_url = (
            f"{invoice['host']}{invoice['unique']}"
        )

        if order.return_url:
            checkout_url += (
                f"?redirectUrl={order.return_url}"
            )

        return Response(
            {
                "success": True,
                "order_id": str(order.uuid),
                "account": order.account,
                "amount": order.amount,
                "purpose": order.purpose,
                "status": order.status,
                "checkout_url": checkout_url,
                "valid_to": invoice.get("validTo"),
            },
            status=status.HTTP_201_CREATED,
        )


class PlumCheckWebhookAPIView(APIView):

    authentication_classes = [
        PlumBasicAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = PlumCheckSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        account = data["fields"].get("account")

        if not account:
            return Response(
                {
                    "success": False,
                    "code": -1,
                    "message": "Account is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = PlumWebhookService.check(
                account=account,
                amount=data["amount"],
            )

        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "code": -1,
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.uuid),
                "success": True,
                "code": 0,
                "message": "Success",
                "accounts": {
                    "amount": str(order.amount),
                    "fullName": order.user_full_name,
                    "username": order.account,
                    "purpose": order.purpose,
                },
            },
            status=status.HTTP_200_OK,
        )

class PlumPerformWebhookAPIView(APIView):

    authentication_classes = [
        PlumBasicAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = PlumPerformSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        order = (
            Order.objects
            .select_for_update()
            .filter(
                uuid=data["id"],
            )
            .first()
        )

        if order is None:
            return Response(
                {
                    "id": str(data["id"]),
                    "success": False,
                    "code": -1,
                    "message": "Order not found.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Idempotency
        if order.status == "paid":
            return Response(
                {
                    "id": str(order.uuid),
                    "success": True,
                    "code": 0,
                    "message": "Success",
                },
                status=status.HTTP_200_OK,
            )

        try:
            PlumWebhookService.perform(
                order=order,
                transaction_id=data["transactionId"],
                card_number=data.get(
                    "cardNumber",
                    "",
                ),
                transaction_date=data["date"],
            )

        except ValueError as exc:
            return Response(
                {
                    "id": str(order.uuid),
                    "success": False,
                    "code": -1,
                    "message": str(exc),
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {
                    "id": str(order.uuid),
                    "success": False,
                    "code": -1,
                    "message": "Payment processing failed.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "id": str(order.uuid),
                "success": True,
                "code": 0,
                "message": "Success",
            },
            status=status.HTTP_200_OK,
        )
