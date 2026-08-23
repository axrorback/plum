from django.urls import path

from .views import CreateOrderAPIView , PlumWebhookAPIView

urlpatterns = [
    path("order/",CreateOrderAPIView.as_view(),name="create-order"),
    path("webhook/",PlumWebhookAPIView.as_view(),name="webhook"),
]