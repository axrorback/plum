from django.db import transaction
from django.utils import timezone
from config import settings
import requests
from .models import Order,OrderStatus,PaymentTransaction,PaymentTransactionStatus


class PlumPaymentService:
    CREATE_INVOICE_URL= "https://business.myuzcard.uz/api-business/Merchant/createMerchantTransaction/"

    @staticmethod
    def find_order_for_check(
            *,
            account: str,
            amount: int,
    ) -> Order:

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
            raise ValueError(
                "Order not found."
            )

        if order.amount != amount:
            raise ValueError(
                "Amount mismatch."
            )

        return order

    @staticmethod
    @transaction.atomic
    def perform(
        *,
        order: Order,
        transaction_id: str,
        amount: int,
        card_number: str,
        transaction_date,
    ) -> PaymentTransaction:

        if order.amount != amount:
            raise ValueError(
                "Amount mismatch."
            )

        existing_transaction = (
            PaymentTransaction.objects
            .filter(
                transaction_id=transaction_id,
            )
            .first()
        )

        if existing_transaction:
            return existing_transaction

        payment = PaymentTransaction.objects.create(
            order=order,
            transaction_id=transaction_id,
            card_number=card_number,
            amount=amount,
            transaction_date=transaction_date,
            status=PaymentTransactionStatus.SUCCESS,
        )

        order.status = OrderStatus.PAID
        order.paid_at = timezone.now()

        order.save(
            update_fields=[
                "status",
                "paid_at",
                "updated_at",
            ]
        )

        return payment

    @classmethod
    def create_invoice(cls, order):
        payload = {
            "merchantId": settings.PLUM_MERCHANT_ID,
            "fields": {
                "account": order.account,
                "amount": order.amount,
            },
        }

        response = requests.post(
            cls.CREATE_INVOICE_URL,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise ValueError(
                str(data["error"])
            )

        result = data["result"]

        order.plum_invoice_id = result["id"]
        order.plum_unique = result["unique"]
        order.plum_valid_to = result["validTo"]

        order.save(
            update_fields=[
                "plum_invoice_id",
                "plum_unique",
                "plum_valid_to",
                "updated_at",
            ]
        )

        return result



class PlumWebhookService:

    @staticmethod
    def check(
        *,
        account: str,
        amount: int,
    ) -> Order:

        return PlumPaymentService.find_order_for_check(
            account=account,
            amount=amount,
        )

    @staticmethod
    def perform(
        *,
        order: Order,
        transaction_id: str,
        card_number: str,
        transaction_date,
    ) -> PaymentTransaction:

        return PlumPaymentService.perform(
            order=order,
            transaction_id=transaction_id,
            amount=order.amount,
            card_number=card_number,
            transaction_date=transaction_date,
        )