from rest_framework import generics

from .models import Cuadro
from .serializers import CuadroSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from . import cuadro_token_service


import json
import os
from subprocess import Popen, PIPE
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# Make sure to import your user model
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()

class HardhatWalletView(APIView):
    # This ensures only authenticated users can access the endpoint
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Get the path to the Node.js script relative to the project root
            # This is more robust than a hardcoded absolute path
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
            node_script_path = os.path.join(scripts_dir, 'generateWallet.cjs')

            # Step 1: Call the Node.js script to generate a wallet
            node_process = Popen(['node', node_script_path], stdout=PIPE, stderr=PIPE, cwd=scripts_dir)
            stdout, stderr = node_process.communicate()

            if node_process.returncode != 0:
                error_message = stderr.decode('utf-8').strip()
                print(f"Node.js script failed with error:\n{error_message}")
                return Response(
                    {"error": f"Failed to generate wallet: {error_message}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Step 2: Parse the JSON output from the Node.js script
            wallet_data = json.loads(stdout.decode('utf-8'))
            private_key = wallet_data['privateKey']
            address = wallet_data['address']

            # Step 3: Securely store the private key (OFF-CHAIN)
            # This is the most critical step. Your implementation here will vary
            # depending on your chosen secret management service (AWS Secrets Manager, etc.).
            # Example placeholder:
            # store_private_key_securely(private_key, request.user.id)
            print(f"Generated Address for user {request.user.id}: {address}")
            print(f"Private Key (for secure storage): {private_key}")

            # Step 4: Save the public address to your database
            # Assuming your user model has an 'ethereum_address' field
            request.user.ethereum_address = address
            request.user.save()
            print(f"Address {address} saved for user {request.user.id}")

            return Response(
                {"address": address,
                 "private_key": private_key
            },

                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateCuadroView(generics.CreateAPIView):
    """
    Endpoint para crear un nuevo cuadro y generar la distribución de tokens.
    """
    queryset = Cuadro.objects.all()
    serializer_class = CuadroSerializer



class ContractInfoView(APIView):
    def get(self, request):
        try:
            info = cuadro_token_service.get_info()
            return Response(info)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class DistribuirTokensView(APIView):
    def post(self, request):
        try:
            receipt = cuadro_token_service.distribuir_tokens()
            return Response({
                'status': 'success',
                'transaction_hash': receipt.transactionHash.hex(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class CertificarPropiedadView(APIView):
    def post(self, request):
        nuevo_propietario = request.data.get('nuevo_propietario')
        cantidad = request.data.get('cantidad')
        if not nuevo_propietario or not cantidad:
            return Response({'error': 'Faltan parametros'}, status=400)
        
        try:
            cantidad = int(cantidad)
            receipt = cuadro_token_service.certificar_propiedad(nuevo_propietario, cantidad)
            return Response({
                'status': 'success',
                'transaction_hash': receipt.transactionHash.hex(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class BalanceView(APIView):
    def get(self, request):
        address = request.query_params.get('address')
        if not address:
            return Response({'error': 'Falta la direccion'}, status=400)
        
        try:
            balance = cuadro_token_service.get_balance(address)
            return Response({'address': address, 'balance': balance})
        except Exception as e:
            return Response({'error': str(e)}, status=500)