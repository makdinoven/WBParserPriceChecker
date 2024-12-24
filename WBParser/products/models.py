from django.db import models

class Product(models.Model):
    article = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
