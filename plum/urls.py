from django.urls import path

from .views import CreateOrderAPIView , PlumCheckWebhookAPIView , PlumPerformWebhookAPIView

urlpatterns = [
    path("order/",CreateOrderAPIView.as_view(),name="create-order"),
    path("webhook/check/",PlumCheckWebhookAPIView.as_view(),name="webhook_check"),
    path("webhook/perform/",PlumPerformWebhookAPIView.as_view(),name="webhook_perform"),
]