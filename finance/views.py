from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Transaccion, CuentaComitente, TokenHolding
from blockchain.models import CuadroToken
from .serializers import (
    TransaccionSerializer, CuentaComitenteSerializer, 
    CuentaComitenteUpdateSerializer, BuyTokensSerializer, 
    TokenHoldingSerializer, UserTokenHoldingSerializer, 
    DonationSerializer, FundProjectSerializer
)
from fondiart_api.models import Artwork, User, Project
from decimal import Decimal

class FundProjectView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FundProjectSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        amount = serializer.validated_data['amount']
        funder = request.user

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            funder_account = CuentaComitente.objects.get(user=funder)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'Funding user does not have a brokerage account.'}, status=status.HTTP_400_BAD_REQUEST)

        commission = amount * Decimal('0.02')
        total_cost = amount + commission

        if funder_account.balance < total_cost:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Update balances
            funder_account.balance -= total_cost
            funder_account.save()

            project.amount_raised += amount
            project.save()

            # Record the transaction
            Transaccion.objects.create(
                cuenta=funder_account,
                tipo=Transaccion.TipoTransaccion.FINANCIACION_PROYECTO,
                monto_pesos=total_cost,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

        return Response({'message': f"Successfully funded project '{project.title}' with {amount}."})

class DonationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DonationSerializer


    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artist_id = serializer.validated_data['artist_id']
        amount = serializer.validated_data['amount']
        donor = request.user

        if donor.id == artist_id:
            return Response({'error': 'You cannot donate to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            artist = User.objects.get(pk=artist_id, role='artist')
        except User.DoesNotExist:
            return Response({'error': 'Artist not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            donor_account = CuentaComitente.objects.get(user=donor)
            artist_account = CuentaComitente.objects.get(user=artist)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'Brokerage account not found for donor or artist.'}, status=status.HTTP_400_BAD_REQUEST)

        commission = amount * Decimal('0.02')
        final_cost = amount + commission

        if donor_account.balance < final_cost:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Perform the transaction
            donor_account.balance -= final_cost
            donor_account.save()

            artist_account.balance += amount
            artist_account.save()

            # Record the transaction for the donor
            Transaccion.objects.create(
                cuenta=donor_account,
                tipo=Transaccion.TipoTransaccion.DONACION_ENVIADA,
                monto_pesos=final_cost,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

            # Record the transaction for the artist
            Transaccion.objects.create(
                cuenta=artist_account,
                tipo=Transaccion.TipoTransaccion.DONACION_RECIBIDA,
                monto_pesos=amount,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

        return Response({'message': 'Donation successful.'}, status=status.HTTP_200_OK)

class UserTokenHoldingsView(generics.ListAPIView):
    serializer_class = UserTokenHoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return TokenHolding.objects.filter(user_id=user_id)

class BuyTokensView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BuyTokensSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        artwork_id = serializer.validated_data['artwork_id']
        quantity = serializer.validated_data['quantity']
        user = request.user

        try:
            artwork = Artwork.objects.select_related('cuadro_token').get(pk=artwork_id)
            token = artwork.cuadro_token
        except (Artwork.DoesNotExist, CuadroToken.DoesNotExist):
            return Response({'error': 'Artwork or token not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            cuenta_comitente = CuentaComitente.objects.get(user=user)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'User does not have a brokerage account.'}, status=status.HTTP_400_BAD_REQUEST)

        if token.tokens_disponibles < quantity:
            return Response({'error': 'Not enough tokens available for sale.'}, status=status.HTTP_400_BAD_REQUEST)

        token_price = artwork.fractionFrom
        total_price = token_price * quantity
        commission = total_price * Decimal('0.02')
        final_cost = total_price + commission

        if cuenta_comitente.balance < final_cost:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            cuenta_comitente.balance -= final_cost
            cuenta_comitente.save()

            token.tokens_disponibles -= quantity
            token.tokens_vendidos += quantity
            token.save()

            holding, created = TokenHolding.objects.get_or_create(
                user=user,
                token=token,
                defaults={'quantity': 0, 'purchase_price': token_price}
            )
            if not created:
                # Simple average for now, a more complex logic could be implemented
                holding.purchase_price = ((holding.purchase_price * holding.quantity) + (token_price * quantity)) / (holding.quantity + quantity)
                holding.quantity += quantity
                holding.save()
            else:
                holding.quantity = quantity
                holding.save()


            # Create a transaction record
            Transaccion.objects.create(
                cuenta=cuenta_comitente,
                tipo=Transaccion.TipoTransaccion.COMPRA,
                artwork=artwork,
                cantidad_tokens=quantity,
                monto_pesos=final_cost,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

            response_serializer = TokenHoldingSerializer(holding)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

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
