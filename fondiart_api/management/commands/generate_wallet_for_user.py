from django.core.management.base import BaseCommand, CommandError
from fondiart_api.models import User, Wallet
from eth_account import Account

class Command(BaseCommand):
    help = 'Generates a wallet for a user who does not have one.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email address of the user to generate a wallet for.')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist.')

        if hasattr(user, 'wallet'):
            self.stdout.write(self.style.WARNING(f'User {email} already has a wallet: {user.wallet.address}'))
            return

        self.stdout.write(f"Generating new wallet for user: {user.email}...")

        # Generate wallet
        account = Account.create()
        
        # Save wallet to the database
        wallet = Wallet.objects.create(
            user=user,
            address=account.address,
            private_key=account.key.hex()
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created wallet for {user.email}'))
        self.stdout.write(f'  Address: {wallet.address}')
        self.stdout.write(f'  (Note: Private key is stored securely in the database)')
