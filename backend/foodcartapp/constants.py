from django.db.models import TextChoices


class PaymentMethod(TextChoices):
    CASH = "cash", "Наличными"
    ONLINE = "online", "Электронно"


class OrderStatus(TextChoices):
    UNPROCESSED = "unprocessed", "Необработанный"
    IN_RESTAURANT = "in_restaurant", "Готовится в ресторане"
    IN_DELIVERY = "in_delivery", "У курьера"
    PROCESSED = "processed", "Обработанный"
