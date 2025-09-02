from django.db import models

class Cuadro(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    artist_wallet = models.CharField(max_length=42) # Dirección de billetera de Ethereum
    total_tokens = models.PositiveIntegerField()
    artist_tokens = models.PositiveIntegerField(default=0)
    platform_tokens = models.PositiveIntegerField(default=0)
    investor_tokens = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title