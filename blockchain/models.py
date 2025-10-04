from django.db import models
from fondiart_api.models import Artwork

class CuadroToken(models.Model):
    artwork = models.OneToOneField(Artwork, on_delete=models.CASCADE, related_name='cuadro_token')
    contract_address = models.CharField(max_length=42, unique=True)
    token_name = models.CharField(max_length=255)
    token_symbol = models.CharField(max_length=10)
    total_supply = models.PositiveIntegerField()
    tokens_disponibles = models.PositiveIntegerField(default=30000)
    tokens_vendidos = models.PositiveIntegerField(default=70000)
    deployment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.artwork.title} at {self.contract_address}"
