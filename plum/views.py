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
from .responses import plum_error_response


class CreateOrderAPIView(APIView):

    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        order = Order.objects.create(
            account=data["account"],
            amount=data["amount"],
            purpose=data["purpose"],
            user_full_name=data["full_name"],
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

        # Only account is required from fields.
        account = data["fields"].get("account")

        if not account:
            return plum_error_response(
                field="account",
                uz="Hisob raqami kiritilishi shart.",
                ru="Необходимо указать номер счёта.",
                en="Account is required.",
            )

        amount = data["amount"]

        # amount=0 is used by Plum for balance/account check.
        if amount == 0:
            return self._balance(
                account=account,
            )

        try:
            order = PlumWebhookService.check(
                account=account,
                amount=amount,
            )

        except ValueError:
            return plum_error_response(
                field="amount",
                uz="Ushbu summa bo‘yicha qarzdorlik topilmadi.",
                ru="Задолженность по данной сумме не найдена.",
                en="No debt was found for this amount.",
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

    def _balance(self, *, account: str):
        order = (
            Order.objects
            .filter(
                account=account,
                status=OrderStatus.PENDING,
            )
            .order_by("-created_at")
            .first()
        )

        if order is None:
            return plum_error_response(
                field="amount",
                uz="Bu oy uchun qarzdorligingiz yo‘q. O‘z vaqtida to‘lov qilganingiz uchun rahmat.",
                ru="В этом месяце у вас нет задолженности. Спасибо за своевременную оплату.",
                en="You have no debt this month. Thank you for your timely payment.",
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
            return plum_error_response(
                field="id",
                uz="Buyurtma topilmadi.",
                ru="Заказ не найден.",
                en="Order not found.",
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

        except ValueError:
            return plum_error_response(
                field="id",
                uz="To‘lov ma’lumotlari noto‘g‘ri.",
                ru="Некорректные данные платежа.",
                en="Invalid payment data.",
            )

        except Exception:
            return plum_error_response(
                field="id",
                uz="To‘lovni qayta ishlashda xatolik yuz berdi.",
                ru="Произошла ошибка при обработке платежа.",
                en="Payment processing failed.",
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