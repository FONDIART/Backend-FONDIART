from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CuentaComitente

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_cuenta_comitente(sender, instance, created, **kwargs):
    if created:
        CuentaComitente.objects.create(user=instance)
