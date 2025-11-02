from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Donation, Transaccion, CuentaComitente
from fondiart_api.models import Project

@receiver(post_save, sender=Donation)
def handle_donation(sender, instance, created, **kwargs):
    if created:
        project = instance.project
        
        # Update amount_raised on the project
        project.amount_raised += instance.amount
        project.save()

        # Check if funding goal is met and funds have not been disbursed yet
        if project.amount_raised >= project.funding_goal and not project.funds_disbursed:
            artist = project.artist
            try:
                artist_account = artist.cuenta_comitente
            except CuentaComitente.DoesNotExist:
                # If the artist doesn't have an account, we can't proceed.
                # You might want to log this error.
                return

            # Transfer funds to artist's account
            amount_to_transfer = project.amount_raised
            artist_account.balance += amount_to_transfer
            artist_account.save()

            # Create a transaction record
            Transaccion.objects.create(
                cuenta=artist_account,
                tipo=Transaccion.TipoTransaccion.FINANCIACION_RECIBIDA,
                monto_pesos=amount_to_transfer,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

            # Mark project as disbursed
            project.funds_disbursed = True
            project.save()