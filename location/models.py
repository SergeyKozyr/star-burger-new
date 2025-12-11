from django.db import models


class Location(models.Model):
    address = models.CharField(max_length=300, unique=True)
    latitude = models.DecimalField(decimal_places=2, max_digits=6)
    longitude = models.DecimalField(decimal_places=2, max_digits=6)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Место на карте"
        verbose_name_plural = "Места на карте"

    def __str__(self) -> str:
        return self.address
