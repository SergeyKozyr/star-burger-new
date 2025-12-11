from typing import Any

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.serializers import ModelSerializer

from foodcartapp.models import Order, OrderItem
from foodcartapp.serializers.order_item import CreateOrderItemSerializer


class CreateOrderSerializer(ModelSerializer):
    products = CreateOrderItemSerializer(many=True, write_only=True, allow_empty=False)
    phonenumber = PhoneNumberField()

    class Meta:
        model = Order
        fields = ("id", "firstname", "lastname", "phonenumber", "address", "products")

    def create(self, validated_data: dict[str, Any]) -> Order:
        items = validated_data.pop("products")
        order = Order.objects.create(**validated_data)
        print(1 / 0)
        order_items = [
            OrderItem(order=order, price=item["quantity"] * item["product"].price, **item)
            for item in items
        ]
        OrderItem.objects.bulk_create(order_items)
        return order
