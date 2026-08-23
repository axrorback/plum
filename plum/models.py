import uuid
from django.db import models

class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentTransactionStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REVERSED = "reversed", "Reversed"


class Order(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False,)
    account = models.CharField(max_length=255,db_index=True,)
    amount = models.PositiveBigIntegerField()
    purpose = models.CharField(max_length=500,)
    user_full_name = models.CharField(max_length=255,)
    return_url = models.URLField(blank=True,)
    callback_url = models.URLField(blank=True,)
    status = models.CharField(max_length=20,choices=OrderStatus,default=OrderStatus.PENDING,db_index=True,)
    paid_at = models.DateTimeField(null=True,blank=True,)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)
    plum_invoice_id = models.BigIntegerField(null=True,blank=True)
    plum_unique = models.CharField(max_length=255,null=True,blank=True,unique=True,)
    plum_valid_to = models.DateTimeField(null=True,blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.account} - {self.amount}"


class PaymentTransaction(models.Model):
    order = models.ForeignKey(Order,on_delete=models.PROTECT,related_name="transactions")
    transaction_id = models.CharField(max_length=255,unique=True,db_index=True,)
    card_number = models.CharField(max_length=32,blank=True,)
    amount = models.PositiveBigIntegerField()
    transaction_date = models.DateTimeField(null=True,blank=True,)
    status = models.CharField(max_length=20,choices=PaymentTransactionStatus,default=PaymentTransactionStatus.SUCCESS,)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.transaction_id