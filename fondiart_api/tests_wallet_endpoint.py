
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Wallet

class UserWalletAddressViewTest(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')
        # Create a wallet for the user
        self.wallet = Wallet.objects.create(user=self.user, address='0x1234567890123456789012345678901234567890', private_key='a_private_key')
        # Authenticate the client
        self.client.force_authenticate(user=self.user)

    def test_get_wallet_address_successfully(self):
        """
        Ensure we can retrieve the wallet address for a given user.
        """
        # Generate the URL for the endpoint
        url = reverse('user-wallet-address', kwargs={'user_id': self.user.id})
        
        # Make the GET request
        response = self.client.get(url)
        
        # Assert the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert the response contains the correct address
        self.assertEqual(response.data['address'], self.wallet.address)

    def test_get_wallet_for_nonexistent_user(self):
        """
        Ensure a 404 is returned when requesting a wallet for a user that does not exist.
        """
        # An ID that does not exist
        non_existent_user_id = 999
        url = reverse('user-wallet-address', kwargs={'user_id': non_existent_user_id})
        
        response = self.client.get(url)
        
        # The view raises Http404, which DRF turns into a 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_fails(self):
        """
        Ensure unauthenticated requests are denied.
        """
        # Log out the user
        self.client.force_authenticate(user=None)
        
        url = reverse('user-wallet-address', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        # Assert that the request was not successful
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
