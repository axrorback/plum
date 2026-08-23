from django.contrib import admin
from .models import Order , PaymentTransaction


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("uuid","account","amount","status","created_at",)

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("order","transaction_id","amount","status","created_at",)