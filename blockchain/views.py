from rest_framework import generics
from .models import Cuadro
from .serializers import CuadroSerializer

class CreateCuadroView(generics.CreateAPIView):
    """
    Endpoint para crear un nuevo cuadro y generar la distribución de tokens.
    """
    queryset = Cuadro.objects.all()
    serializer_class = CuadroSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from . import cuadro_token_service

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