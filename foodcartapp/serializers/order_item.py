from rest_framework.fields import IntegerField
from rest_framework.serializers import ModelSerializer

from foodcartapp.models import OrderItem


class CreateOrderItemSerializer(ModelSerializer):
    quantity = IntegerField(min_value=1, default=1)

    class Meta:
        model = OrderItem
        fields = ("product", "quantity")
