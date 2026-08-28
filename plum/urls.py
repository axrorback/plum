from django.urls import path, re_path

from .views import (
    CreateOrderAPIView,
    PlumCheckWebhookAPIView,
    PlumPerformWebhookAPIView,
)

urlpatterns = [
    path("order/", CreateOrderAPIView.as_view(), name="create-order"),

    re_path(
        r"^webhook/check/?$",
        PlumCheckWebhookAPIView.as_view(),
        name="webhook_check",
    ),

    re_path(
        r"^webhook/perform/?$",
        PlumPerformWebhookAPIView.as_view(),
        name="webhook_perform",
    ),
]