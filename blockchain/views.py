import subprocess
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from fondiart_api.models import Artwork, Wallet
from rest_framework.permissions import IsAuthenticated
from fondiart_api.permissions import IsAdminRoleUser
from .models import CuadroToken
from .cuadro_token_service import deploy_and_tokenize, transfer_tokens
from .serializers import CuadroTokenSerializer, TransferTokensSerializer, CuadroTokenDetailSerializer
import os
from django.db import transaction
from fondiart_api.models import User
from finance.models import TokenHolding
from rest_framework.views import APIView

class CuadroTokenListView(generics.ListAPIView):
    queryset = CuadroToken.objects.all()
    serializer_class = CuadroTokenDetailSerializer
    permission_classes = []

class TokenizeArtworkView(generics.GenericAPIView):
    permission_classes = [IsAdminRoleUser]
    serializer_class = CuadroTokenSerializer

    def post(self, request, *args, **kwargs):
        print("\n--- [DEBUG] TokenizeArtworkView: START ---")
        print(f"[DEBUG] Payload: {request.data}")

        artwork_id = request.data.get('artwork_id')
        if not artwork_id:
            print("[DEBUG] ERROR: Artwork ID is required.")
            return Response({'error': 'Artwork ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        print(f"[DEBUG] Fetching Artwork with ID: {artwork_id}")
        artwork = get_object_or_404(Artwork, pk=artwork_id)
        print(f"[DEBUG] Found Artwork: '{artwork.title}' (ID: {artwork.id})")
        
        admin_user = request.user
        print(f"[DEBUG] Admin User: {admin_user.email} (ID: {admin_user.id})")

        try:
            print("[DEBUG] Checking for admin wallet...")
            admin_wallet = Wallet.objects.get(user_id=admin_user.id)
            print(f"[DEBUG] SUCCESS: Admin wallet found: {admin_wallet.address}")
        except Wallet.DoesNotExist:
            print("[DEBUG] ERROR: Admin wallet not found.")
            return Response({'error': 'Admin user does not have an associated wallet.'}, status=status.HTTP_400_BAD_REQUEST)

        print(f"[DEBUG] Checking for artist wallet for artist: {artwork.artist.email} (ID: {artwork.artist.id})")
        if not Wallet.objects.filter(user_id=artwork.artist.id).exists():
            print("[DEBUG] ERROR: Artist wallet not found.")
            return Response({'error': 'Artist does not have an associated wallet.'}, status=status.HTTP_400_BAD_REQUEST)
        print("[DEBUG] SUCCESS: Artist wallet found.")

        # No es necesario comprobar si ya está tokenizado, ya que update_or_create lo manejará
        print("[DEBUG] Proceeding to service call.")

        try:
            contract_address = deploy_and_tokenize(artwork, admin_wallet.address)
            
            print(f"[DEBUG] Service returned contract address: {contract_address}")
            artwork.contract_address = contract_address
            artwork.save()
            print(f"[DEBUG] Saved contract address to Artwork ID: {artwork.id}")

            # Usar update_or_create para manejar atómicamente la creación/actualización del token
            token_defaults = {
                'contract_address': contract_address,
                'token_name': f"{artwork.title} Token",
                'token_symbol': f"ART{artwork.id}",
                'total_supply': 100000,
            }
            
            token_instance, created = CuadroToken.objects.update_or_create(
                artwork=artwork,
                defaults=token_defaults
            )
            print(f"[DEBUG] update_or_create successful. Token was created: {created}")

            serializer = self.get_serializer(token_instance)
            print("[DEBUG] Serialization successful. Returning 201 CREATED.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except subprocess.CalledProcessError as e:
            error_message = f"Failed to execute deployment script. Return code: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            print(f"[DEBUG] ERROR: Subprocess failed.\n{error_message}")
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f"[DEBUG] ERROR: An unexpected exception occurred.\n{str(e)}")
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransferTokensView(generics.GenericAPIView):
    permission_classes = [IsAdminRoleUser]
    serializer_class = TransferTokensSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        contract_address = validated_data['contract_address']
        to_address = validated_data['to_address']
        amount = validated_data['amount']

        try:
            result = transfer_tokens(contract_address, to_address, amount)
            return Response({'status': 'success', 'message': 'Transaction sent successfully.', 'details': result}, status=status.HTTP_200_OK)

        except subprocess.CalledProcessError as e:
            error_message = f"Failed to execute transfer script. Return code: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetContractAddressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        artwork_id = self.kwargs.get('artwork_id')
        token = get_object_or_404(CuadroToken, artwork_id=artwork_id)
        return Response({'contract_address': token.contract_address}, status=status.HTTP_200_OK)

class InitialTokenDistributionView(APIView):
    permission_classes = [IsAdminRoleUser]

    def post(self, request, *args, **kwargs):
        artwork_id = kwargs.get('artwork_id')
        artwork = get_object_or_404(Artwork, pk=artwork_id)
        cuadro_token = get_object_or_404(CuadroToken, artwork=artwork)
        
        artist = artwork.artist
        admin_user = User.objects.filter(role='admin').first()

        if not admin_user:
            return Response({'error': 'No admin user found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        distributions = [
            {'user': artist, 'amount': 60000},
            {'user': admin_user, 'amount': 10000}
        ]

        try:
            with transaction.atomic():
                for dist in distributions:
                    TokenHolding.objects.create(
                        user=dist['user'],
                        token=cuadro_token,
                        quantity=dist['amount'],
                        purchase_price=0
                    )

            return Response({"status": "success", "message": "Initial token holdings recorded successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
