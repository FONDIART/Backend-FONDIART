import subprocess
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from fondiart_api.models import Artwork
from rest_framework.permissions import IsAuthenticated
from fondiart_api.permissions import IsAdminRoleUser
from .models import CuadroToken
from .serializers import CuadroTokenSerializer
from .cuadro_token_service import deploy_and_tokenize

class TokenizeArtworkView(generics.GenericAPIView):
    permission_classes = [IsAdminRoleUser]
    serializer_class = CuadroTokenSerializer

    def post(self, request, *args, **kwargs):
        artwork_id = request.data.get('artwork_id')
        if not artwork_id:
            return Response({'error': 'Artwork ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        artwork = get_object_or_404(Artwork, pk=artwork_id)
        admin_user = request.user

        # Verify wallets exist
        if not hasattr(admin_user, 'wallet'):
            return Response({'error': 'Admin user does not have an associated wallet.'}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(artwork.artist, 'wallet'):
            return Response({'error': 'Artist does not have an associated wallet.'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(artwork, 'cuadro_token'):
            return Response({'error': 'This artwork has already been tokenized.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Pass the artwork and the admin's wallet address to the service
            contract_address = deploy_and_tokenize(artwork, admin_user.wallet.address)
            
            token_data = {
                'artwork': artwork.id,
                'contract_address': contract_address,
                'token_name': f"{artwork.title} Token",
                'token_symbol': f"ART{artwork.id}",
                'total_supply': artwork.fractionsTotal,
            }
            
            serializer = self.get_serializer(data=token_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except subprocess.CalledProcessError as e:
            error_message = f"Failed to execute deployment script. Return code: {e.returncode}\n"
            error_message += f"Stdout: {e.stdout}\n"
            error_message += f"Stderr: {e.stderr}"
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetContractAddressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        artwork_id = self.kwargs.get('artwork_id')
        token = get_object_or_404(CuadroToken, artwork_id=artwork_id)
        return Response({'contract_address': token.contract_address}, status=status.HTTP_200_OK)
