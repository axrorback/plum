from django.db import transaction
from django.utils import timezone
from config import settings
import requests
from .models import Order,OrderStatus,PaymentTransaction,PaymentTransactionStatus
import logging

logger = logging.getLogger(__name__)

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

        print("========== PLUM CREATE INVOICE START ==========", flush=True)

        try:
            payload = {
                "merchantId": 2461,
                "fields": {
                    "account": order.account,
                    "amount": order.amount,
                },
            }

            print(
                f"[PLUM] Payload: {payload}",
                flush=True,
            )

            url = (
                "https://business.myuzcard.uz/"
                "api-business/Merchant/createMerchantTransaction"
            )

            print(
                f"[PLUM] URL: {url}",
                flush=True,
            )

            print(
                "[PLUM] Sending request...",
                flush=True,
            )

            response = requests.post(
                url,
                json=payload,
                timeout=15,
            )

            print(
                f"[PLUM] Response status: {response.status_code}",
                flush=True,
            )

            print(
                f"[PLUM] Response headers: {dict(response.headers)}",
                flush=True,
            )

            print(
                f"[PLUM] Response body: {response.text}",
                flush=True,
            )

            print(
                "[PLUM] Calling raise_for_status()...",
                flush=True,
            )

            response.raise_for_status()

            print(
                "[PLUM] HTTP status is OK",
                flush=True,
            )

            print(
                "[PLUM] Parsing JSON...",
                flush=True,
            )

            data = response.json()

            print(
                f"[PLUM] Parsed JSON: {data}",
                flush=True,
            )

            if data.get("error"):
                print(
                    f"[PLUM] API ERROR: {data['error']}",
                    flush=True,
                )

                raise ValueError(
                    str(data["error"])
                )

            print(
                "[PLUM] Getting result...",
                flush=True,
            )

            result = data["result"]

            print(
                f"[PLUM] Result: {result}",
                flush=True,
            )

            print(
                "[PLUM] Saving invoice data to order...",
                flush=True,
            )

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

            print(
                "[PLUM] Order saved successfully",
                flush=True,
            )

            print(
                "========== PLUM CREATE INVOICE SUCCESS ==========",
                flush=True,
            )

            return result

        except Exception as exc:

            print(
                "========== PLUM CREATE INVOICE ERROR ==========",
                flush=True,
            )

            print(
                f"[PLUM] Exception type: {type(exc).__name__}",
                flush=True,
            )

            print(
                f"[PLUM] Exception: {exc}",
                flush=True,
            )

            import traceback

            traceback.print_exc()

            print(
                "=================================================",
                flush=True,
            )

            raise



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