from django.db import models
from django.conf import settings

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

    cuenta = models.ForeignKey(
        CuentaComitente,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    tipo = models.CharField(
        max_length=10,
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

    def __str__(self):
        return f"{self.tipo} - {self.cuenta.user.username} - {self.monto_pesos}"