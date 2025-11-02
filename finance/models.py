from django.db import models
from django.conf import settings
from blockchain.models import CuadroToken

class TokenHolding(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_holdings')
    token = models.ForeignKey(CuadroToken, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} holds {self.quantity} of {self.token.token_symbol}"

class CuentaComitente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cuenta_comitente'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    def __str__(self):
        return f"Cuenta de {self.user.username} - Saldo: {self.balance}"

class Transaccion(models.Model):
    class TipoTransaccion(models.TextChoices):
        COMPRA = 'COMPRA', 'Compra de Tokens'
        VENTA = 'VENTA', 'Venta de Tokens'
        DEPOSITO = 'DEPOSITO', 'Depósito de Pesos'
        RETIRO = 'RETIRO', 'Retiro de Pesos'
        DONACION_ENVIADA = 'DONACION_ENVIADA', 'Donación Enviada'
        DONACION_RECIBIDA = 'DONACION_RECIBIDA', 'Donación Recibida'
        FINANCIACION_PROYECTO = 'FINANCIACION_PROYECTO', 'Financiación de Proyecto'
        FINANCIACION_RECIBIDA = 'FINANCIACION_RECIBIDA', 'Financiación Recibida'

    cuenta = models.ForeignKey(
        CuentaComitente,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    tipo = models.CharField(
        max_length=25,
        choices=TipoTransaccion.choices
    )
    # Assuming 'Artwork' is the model for the tokenized asset
    # We allow it to be null for deposits/withdrawals
    artwork = models.ForeignKey(
        'fondiart_api.Artwork',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cantidad_tokens = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True
    )
    monto_pesos = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    fecha = models.DateTimeField(auto_now_add=True)
    
    class EstadoTransaccion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        COMPLETADA = 'COMPLETADA', 'Completada'
        FALLIDA = 'FALLIDA', 'Fallida'

    estado = models.CharField(
        max_length=10,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.PENDIENTE
    )
    recipient_artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_donations')

    def __str__(self):
        return f"{self.tipo} - {self.cuenta.user.username} - {self.monto_pesos}"

class Donation(models.Model):
    project = models.ForeignKey('fondiart_api.Project', on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation of {self.amount} to {self.project.title} by {self.donor.username}"

class SellOrder(models.Model):
    STATUS_CHOICES = (
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
        ('cancelada', 'Cancelada'),
    )

    token = models.ForeignKey(CuadroToken, on_delete=models.CASCADE, related_name='sell_orders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sell_orders')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    publication_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='abierta')

    def __str__(self):
        return f"Sell order for {self.quantity} of {self.token.token_symbol} by {self.user.username}"