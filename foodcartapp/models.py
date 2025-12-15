from collections import defaultdict

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, QuerySet
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from foodcartapp.constants import PaymentMethod, OrderStatus

from location.service import LocationService


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(availability=True).values_list("product")
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField("в продаже", default=True, db_index=True)

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self) -> QuerySet["Order"]:
        return self.annotate(total_price=Sum("items__price"))

    def active(self) -> QuerySet["Order"]:
        return self.exclude(status=OrderStatus.PROCESSED)

    def with_available_restaurants(self) -> QuerySet["Order"]:
        restaurants_with_products = defaultdict(set)
        restaurant_items = (
            RestaurantMenuItem.objects.filter(availability=True)
            .select_related("restaurant", "product")
            .iterator()
        )

        for restaurant_item in restaurant_items:
            restaurants_with_products[restaurant_item.restaurant].add(restaurant_item.product.pk)

        for order in self:
            available_restaurants = []
            order_items = set(order.items.values_list("product_id", flat=True))

            for restaurant, products in restaurants_with_products.items():
                if order_items.issubset(products):
                    available_restaurants.append(restaurant)

            order.available_restaurants = available_restaurants

        return self

    def with_distance_to_restaurants(self) -> QuerySet["Order"]:
        location_service = LocationService(geocoder_api_key=settings.YANDEX_GEOCODER_API_KEY)

        for order in self:
            if not hasattr(order, "available_restaurants"):
                continue

            restaurants_with_distances = []

            for restaurant in order.available_restaurants:
                distance = location_service.get_distance_between_addresses(
                    restaurant.address, order.address
                )

                if distance is not None:
                    restaurants_with_distances.append(
                        {"name": restaurant.name, "distance_to_address": distance}
                    )

            order.restaurants_with_distances = sorted(
                restaurants_with_distances, key=lambda r: r["distance_to_address"]
            )

        return self


class Order(models.Model):
    firstname = models.CharField("Имя", max_length=15)
    lastname = models.CharField("Фамилия", max_length=30)
    phonenumber = PhoneNumberField("Номер телефона", max_length=12)
    address = models.CharField("Адрес", max_length=100)
    status = models.CharField(
        "Статус", max_length=13, choices=OrderStatus, default=OrderStatus.UNPROCESSED, db_index=True
    )
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=6,
        choices=PaymentMethod,
        db_index=True,
    )
    comment = models.TextField("Комментарий", blank=True)
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="orders",
        verbose_name="Ресторан, который готовит заказ",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    registered_at = models.DateTimeField(
        "Время создания заказа", default=timezone.now, db_index=True
    )
    called_at = models.DateTimeField("Время звонка", blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField("Время доставки", blank=True, null=True, db_index=True)

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f"{self.firstname} {self.lastname}, {self.address}"

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Заказ", related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, verbose_name="товар", on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.PositiveSmallIntegerField("Количество")
    price = models.DecimalField(
        "Цена", validators=[MinValueValidator(1)], max_digits=6, decimal_places=2
    )

    class Meta:
        verbose_name = "элемент заказа"
        verbose_name_plural = "элементы заказа"

    def __str__(self):
        return f"{self.product} {self.quantity} шт. - {self.order}"
