from django.db.models import TextChoices


class PaymentMethod(TextChoices):
    CASH = "cash", "Наличными"
    ONLINE = "online", "Электронно"


class OrderStatus(TextChoices):
    PROCESSED = "processed", "Обработанный"
    UNPROCESSED = "unprocessed", "Необработанный"
