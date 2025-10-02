from rest_framework import generics, status
from rest_framework.response import Response
from django.db import transaction
from .models import Transaccion, CuentaComitente
from fondiart_api.models import Artwork, User
from .serializers import TransaccionSerializer, CuentaComitenteSerializer, CuentaComitenteUpdateSerializer

class CuentaComitenteCreateView(generics.CreateAPIView):
    serializer_class = CuentaComitenteSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        if not user_id:
            return Response({'error': 'El campo user es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'El usuario no existe.'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'cuenta_comitente'):
            return Response({'error': 'El usuario ya tiene una cuenta comitente.'}, status=status.HTTP_400_BAD_REQUEST)

        cuenta = CuentaComitente.objects.create(user=user)
        serializer = self.get_serializer(cuenta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CuentaComitenteDetailView(generics.RetrieveAPIView):
    serializer_class = CuentaComitenteSerializer

    def get_object(self):
        user = self.request.user
        try:
            return user.cuenta_comitente
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'El usuario no tiene una cuenta comitente.'}, status=status.HTTP_404_NOT_FOUND)

class CuentaComitenteUpdateView(generics.UpdateAPIView):
    serializer_class = CuentaComitenteUpdateSerializer
    queryset = CuentaComitente.objects.all()
    lookup_field = 'user__id'

class CreateTransaccionView(generics.CreateAPIView):
    serializer_class = TransaccionSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        tipo = request.data.get('tipo')
        monto_pesos = request.data.get('monto_pesos')
        artwork_id = request.data.get('artwork')
        cantidad_tokens = request.data.get('cantidad_tokens')

        try:
            cuenta = user.cuenta_comitente
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'El usuario no tiene una cuenta comitente.'}, status=status.HTTP_400_BAD_REQUEST)

        if tipo == Transaccion.TipoTransaccion.COMPRA:
            if not all([monto_pesos, artwork_id, cantidad_tokens]):
                return Response({'error': 'Para la compra se requiere monto_pesos, artwork y cantidad_tokens.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                artwork = Artwork.objects.get(id=artwork_id)
                monto_pesos = float(monto_pesos)

                if cuenta.balance < monto_pesos:
                    return Response({'error': 'Saldo insuficiente.'}, status=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():
                    cuenta.balance -= monto_pesos
                    cuenta.save()

                    # Aquí iría la lógica para transferir los tokens al usuario
                    # Por ejemplo, llamar a un servicio de blockchain

                    transaccion = Transaccion.objects.create(
                        cuenta=cuenta,
                        tipo=tipo,
                        artwork=artwork,
                        cantidad_tokens=cantidad_tokens,
                        monto_pesos=monto_pesos,
                        estado=Transaccion.EstadoTransaccion.COMPLETADA
                    )
                return Response(TransaccionSerializer(transaccion).data, status=status.HTTP_201_CREATED)

            except Artwork.DoesNotExist:
                return Response({'error': 'La obra de arte no existe.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif tipo == Transaccion.TipoTransaccion.VENTA:
            # Lógica para la venta de tokens (requeriría verificar la tenencia de tokens del usuario)
            return Response({'message': 'La lógica de venta aún no está implementada.'}, status=status.HTTP_501_NOT_IMPLEMENTED)

        elif tipo == Transaccion.TipoTransaccion.DEPOSITO:
            if not monto_pesos:
                return Response({'error': 'Para el depósito se requiere monto_pesos.'}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                monto_pesos = float(monto_pesos)
                cuenta.balance += monto_pesos
                cuenta.save()
                transaccion = Transaccion.objects.create(
                    cuenta=cuenta,
                    tipo=tipo,
                    monto_pesos=monto_pesos,
                    estado=Transaccion.EstadoTransaccion.COMPLETADA
                )
            return Response(TransaccionSerializer(transaccion).data, status=status.HTTP_201_CREATED)

        else:
            return Response({'error': 'Tipo de transacción no válido.'}, status=status.HTTP_400_BAD_REQUEST)