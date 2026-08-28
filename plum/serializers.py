from rest_framework import serializers

class PlumWebhookSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=("check", "perform"))


class PlumCheckSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0)
    fields = serializers.DictField()


class PlumPerformSerializer(serializers.Serializer):
    transactionId = serializers.CharField(max_length=255,)
    id = serializers.UUIDField()
    date = serializers.DateTimeField()
    cardNumber = serializers.CharField(max_length=32,allow_blank=True,required=False,)


class CreateOrderSerializer(serializers.Serializer):
    account = serializers.CharField(max_length=255,)
    user_full_name = serializers.CharField(max_length=255,)
    amount = serializers.IntegerField(min_value=1,)
    purpose = serializers.CharField(max_length=500)
    return_url = serializers.URLField(required=False,allow_blank=True,)