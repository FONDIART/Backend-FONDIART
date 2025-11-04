from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from fondiart_api.permissions import IsAdminRoleUser
from rest_framework.response import Response
from django.db import transaction
from .models import Transaccion, CuentaComitente, TokenHolding, Donation, SellOrder
from blockchain.models import CuadroToken
from .serializers import (
    TransaccionSerializer, CuentaComitenteSerializer, 
    CuentaComitenteUpdateSerializer, BuyTokensSerializer, 
    TokenHoldingSerializer, UserTokenHoldingSerializer, 
    DonationSerializer, FundProjectSerializer,
    ProjectDonationSerializer,
    LiquidateArtworkSerializer,
    CheckFundsSerializer,
    SellOrderSerializer,
    BuyFromSellOrderSerializer,
    DonationHistorySerializer,
    DonationTransactionSerializer
)
from fondiart_api.models import Artwork, User, Project
from decimal import Decimal
from django.db.models import Sum, Count

class ProjectDonorsCountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        donors_count = Donation.objects.filter(project_id=project_id).values('donor').distinct().count()

        return Response({
            'donors_count': donors_count,
        })

class ProjectDonationSummaryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, user_id):
        donations = Donation.objects.filter(project_id=project_id, donor_id=user_id)
        summary = donations.aggregate(
            total_donated=Sum('amount'),
            donation_count=Count('id')
        )

        return Response({
            'total_donated': summary['total_donated'] or 0,
            'donation_count': summary['donation_count'] or 0,
        })

class ProjectDonationView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectDonationSerializer

    def perform_create(self, serializer):
        project = serializer.validated_data['project']
        amount = serializer.validated_data['amount']
        donor = self.request.user

        try:
            donor_account = CuentaComitente.objects.get(user=donor)
        except CuentaComitente.DoesNotExist:
            raise serializers.ValidationError("Donor does not have a brokerage account.")

        commission = amount * Decimal('0.02')
        total_cost = amount + commission

        if donor_account.balance < total_cost:
            raise serializers.ValidationError("Insufficient funds.")

        with transaction.atomic():
            donor_account.balance -= total_cost
            donor_account.save()

            Transaccion.objects.create(
                cuenta=donor_account,
                tipo=Transaccion.TipoTransaccion.DONACION_ENVIADA,
                monto_pesos=total_cost,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

            serializer.save(donor=donor)

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
            print(f"[DEBUG] DonationView: Artist found: {artist.name} (ID: {artist.id})")
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
                estado=Transaccion.EstadoTransaccion.COMPLETADA,
                recipient_artist=artist
            )
            print(f"[DEBUG] DonationView: DONACION_ENVIADA created with recipient_artist: {artist.name}")

            # Record the transaction for the artist
            Transaccion.objects.create(
                cuenta=artist_account,
                tipo=Transaccion.TipoTransaccion.DONACION_RECIBIDA,
                monto_pesos=amount,
                estado=Transaccion.EstadoTransaccion.COMPLETADA,
                recipient_artist=artist
            )
            print(f"[DEBUG] DonationView: DONACION_RECIBIDA created with recipient_artist: {artist.name}")

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

        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            return Response({'error': 'Admin user not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            admin_cuenta_comitente = CuentaComitente.objects.get(user=admin_user)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'Admin does not have a brokerage account.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with transaction.atomic():
            cuenta_comitente.balance -= final_cost
            cuenta_comitente.save()

            admin_cuenta_comitente.balance += final_cost
            admin_cuenta_comitente.save()

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

class CheckSufficientFundsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckFundsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        amount = serializer.validated_data['amount']

        try:
            cuenta_comitente = CuentaComitente.objects.get(user_id=user_id)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'User does not have a brokerage account.'}, status=status.HTTP_404_NOT_FOUND)

        has_sufficient_funds = cuenta_comitente.balance >= amount
        
        response_data = {'has_sufficient_funds': has_sufficient_funds}
        print(response_data)
        return Response(response_data)

class TransferToAdminView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckFundsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        amount = serializer.validated_data['amount']

        try:
            user_account = CuentaComitente.objects.get(user_id=user_id)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'User does not have a brokerage account.'}, status=status.HTTP_404_NOT_FOUND)

        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            return Response({'error': 'Admin user not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            admin_account = CuentaComitente.objects.get(user=admin_user)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'Admin does not have a brokerage account.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if user_account.balance < amount:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user_account.balance -= amount
            user_account.save()

            admin_account.balance += amount
            admin_account.save()

            # Create transaction records
            Transaccion.objects.create(
                cuenta=user_account,
                tipo=Transaccion.TipoTransaccion.RETIRO, # Or a new type like 'TRANSFER_TO_ADMIN'
                monto_pesos=amount,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

            Transaccion.objects.create(
                cuenta=admin_account,
                tipo=Transaccion.TipoTransaccion.DEPOSITO, # Or a new type like 'TRANSFER_FROM_USER'
                monto_pesos=amount,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

        return Response({'message': 'Transfer to admin successful.'}, status=status.HTTP_200_OK)

class LiquidateArtworkView(generics.GenericAPIView):
    permission_classes = [IsAdminRoleUser]
    serializer_class = LiquidateArtworkSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artwork_id = serializer.validated_data['artwork_id']
        total_amount = serializer.validated_data['total_amount']

        try:
            artwork = Artwork.objects.get(pk=artwork_id)
            cuadro_token = CuadroToken.objects.get(artwork=artwork)
            artist = artwork.artist
            admin_user = User.objects.filter(role='admin').first()
            admin_account = CuentaComitente.objects.get(user=admin_user)
        except (Artwork.DoesNotExist, CuadroToken.DoesNotExist, User.DoesNotExist, CuentaComitente.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        token_value = total_amount / 100000
        token_holders = TokenHolding.objects.filter(token=cuadro_token)
        
        total_payout = 0
        for holder in token_holders:
            total_payout += (holder.quantity * token_value) * Decimal('0.99')

        if admin_account.balance < total_payout:
            return Response({'error': 'Admin has insufficient funds to liquidate.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Logic to pay token holders
            for holder in token_holders:
                holder_account = CuentaComitente.objects.get(user=holder.user)
                transfer_amount = (holder.quantity * token_value)
                commission = transfer_amount * Decimal('0.01')
                final_transfer_amount = transfer_amount - commission
                
                admin_account.balance -= final_transfer_amount
                holder_account.balance += final_transfer_amount
                
                admin_account.save()
                holder_account.save()

                Transaccion.objects.create(
                    cuenta=admin_account,
                    tipo=Transaccion.TipoTransaccion.VENTA, # Or a new type
                    monto_pesos=final_transfer_amount,
                    estado=Transaccion.EstadoTransaccion.COMPLETADA
                )
                Transaccion.objects.create(
                    cuenta=holder_account,
                    tipo=Transaccion.TipoTransaccion.COMPRA, # Or a new type
                    monto_pesos=final_transfer_amount,
                    estado=Transaccion.EstadoTransaccion.COMPLETADA
                )
                holder.delete()

            # Logic to distribute remaining value
            remaining_tokens = cuadro_token.tokens_disponibles
            if remaining_tokens > 0:
                remaining_value = remaining_tokens * token_value
                distribution_amount = remaining_value / 2
                
                artist_account = CuentaComitente.objects.get(user=artist)

                admin_account.balance -= remaining_value
                artist_account.balance += distribution_amount
                admin_account.balance += distribution_amount

                admin_account.save()
                artist_account.save()

            # Delete the token
            cuadro_token.delete()

        return Response({'message': 'Artwork liquidated successfully.'}, status=status.HTTP_200_OK)

class WithdrawToCBUView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckFundsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        amount = serializer.validated_data['amount']

        try:
            user = User.objects.get(pk=user_id)
            if not user.cbu:
                return Response({'error': 'User does not have a CBU registered.'}, status=status.HTTP_400_BAD_REQUEST)

            user_account = CuentaComitente.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'User does not have a brokerage account.'}, status=status.HTTP_404_NOT_FOUND)

        if user_account.balance < amount:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user_account.balance -= amount
            user_account.save()

            Transaccion.objects.create(
                cuenta=user_account,
                tipo=Transaccion.TipoTransaccion.RETIRO,
                monto_pesos=amount,
                estado=Transaccion.EstadoTransaccion.COMPLETADA
            )

        return Response({'message': 'Withdrawal successful. The amount will be credited to your CBU.'}, status=status.HTTP_200_OK)

class UserTransactionHistoryView(generics.ListAPIView):
    serializer_class = TransaccionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        try:
            cuenta = CuentaComitente.objects.get(user_id=user_id)
            return Transaccion.objects.filter(cuenta=cuenta).order_by('-fecha')
        except CuentaComitente.DoesNotExist:
            return Transaccion.objects.none()

class SellOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = SellOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SellOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        token = serializer.validated_data['token']
        quantity = serializer.validated_data['quantity']
        user = self.request.user

        try:
            holding = TokenHolding.objects.get(user=user, token=token)
            if holding.quantity < quantity:
                raise serializers.ValidationError("Not enough tokens to sell.")
        except TokenHolding.DoesNotExist:
            raise serializers.ValidationError("You do not own this token.")

        serializer.save(user=user)

class SellOrderDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SellOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SellOrder.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'abierta':
            return Response({'error': 'Only open orders can be updated or canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        status_to_update = request.data.get('status')
        if status_to_update:
            if status_to_update != 'cancelada':
                return Response({'error': 'You can only change the status to "cancelada".'}, status=status.HTTP_400_BAD_REQUEST)
            
            instance.status = 'cancelada'
            instance.save()
            return Response(self.get_serializer(instance).data)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data.get('quantity', instance.quantity)
        
        try:
            holding = TokenHolding.objects.get(user=request.user, token=instance.token)
            if holding.quantity < quantity:
                raise serializers.ValidationError("Not enough tokens to sell.")
        except TokenHolding.DoesNotExist:
            raise serializers.ValidationError("You do not own this token.")

        self.perform_update(serializer)
        return Response(serializer.data)

class UserSellOrderListView(generics.ListAPIView):
    serializer_class = SellOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return SellOrder.objects.filter(user_id=user_id)

class OpenSellOrderListView(generics.ListAPIView):
    serializer_class = SellOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = SellOrder.objects.filter(status='abierta')

class BuyFromSellOrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BuyFromSellOrderSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sell_order_id = serializer.validated_data['sell_order_id']
        quantity_to_buy = serializer.validated_data['quantity']
        buyer = request.user

        try:
            sell_order = SellOrder.objects.get(pk=sell_order_id, status='abierta')
        except SellOrder.DoesNotExist:
            return Response({'error': 'Sell order not found or not open.'}, status=status.HTTP_404_NOT_FOUND)

        if sell_order.quantity < quantity_to_buy:
            return Response({'error': 'Not enough tokens in the sell order.'}, status=status.HTTP_400_BAD_REQUEST)

        seller = sell_order.user
        if buyer == seller:
            return Response({'error': 'You cannot buy from your own sell order.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            buyer_account = CuentaComitente.objects.get(user=buyer)
            seller_account = CuentaComitente.objects.get(user=seller)
            admin_user = User.objects.filter(role='admin').first()
            admin_account = CuentaComitente.objects.get(user=admin_user)
        except CuentaComitente.DoesNotExist:
            return Response({'error': 'Brokerage account not found for buyer, seller, or admin.'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sell_order.price * quantity_to_buy
        buyer_commission = total_price * Decimal('0.02')
        buyer_total_cost = total_price + buyer_commission
        seller_commission = total_price * Decimal('0.01')
        seller_net_amount = total_price - seller_commission

        if buyer_account.balance < buyer_total_cost:
            return Response({'error': 'Insufficient funds.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Funds transfer
            buyer_account.balance -= buyer_total_cost
            seller_account.balance += seller_net_amount
            admin_account.balance += buyer_commission + seller_commission
            
            buyer_account.save()
            seller_account.save()
            admin_account.save()

            # Token transfer
            seller_holding = TokenHolding.objects.get(user=seller, token=sell_order.token)
            seller_holding.quantity -= quantity_to_buy
            seller_holding.save()

            buyer_holding, created = TokenHolding.objects.get_or_create(
                user=buyer,
                token=sell_order.token,
                defaults={'quantity': 0, 'purchase_price': sell_order.price}
            )
            if not created:
                # Weighted average for purchase price
                new_quantity = buyer_holding.quantity + quantity_to_buy
                new_purchase_price = ((buyer_holding.purchase_price * buyer_holding.quantity) + (sell_order.price * quantity_to_buy)) / new_quantity
                buyer_holding.purchase_price = new_purchase_price
                buyer_holding.quantity = new_quantity
                buyer_holding.save()
            else:
                buyer_holding.quantity = quantity_to_buy
                buyer_holding.save()

            # Update sell order
            sell_order.quantity -= quantity_to_buy
            if sell_order.quantity == 0:
                sell_order.status = 'cerrada'
            sell_order.save()

            # Transaction records
            Transaccion.objects.create(cuenta=buyer_account, tipo=Transaccion.TipoTransaccion.COMPRA, monto_pesos=buyer_total_cost, estado=Transaccion.EstadoTransaccion.COMPLETADA)
            Transaccion.objects.create(cuenta=seller_account, tipo=Transaccion.TipoTransaccion.VENTA, monto_pesos=seller_net_amount, estado=Transaccion.EstadoTransaccion.COMPLETADA)

        return Response({'message': 'Purchase successful.'}, status=status.HTTP_200_OK)

class UserDonationHistoryView(generics.ListAPIView):
    serializer_class = DonationTransactionSerializer # Changed serializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        print(f"[DEBUG] UserDonationHistoryView: Received user_id: {user_id}")
        try:
            cuenta = CuentaComitente.objects.get(user_id=user_id)
            queryset = Transaccion.objects.filter(
                cuenta=cuenta,
                tipo__in=[Transaccion.TipoTransaccion.DONACION_ENVIADA, Transaccion.TipoTransaccion.DONACION_RECIBIDA]
            ).order_by('-fecha')
            print(f"[DEBUG] UserDonationHistoryView: Queryset SQL: {queryset.query}")
            print(f"[DEBUG] UserDonationHistoryView: Queryset results count: {queryset.count()}")
            return queryset
        except CuentaComitente.DoesNotExist:
            print(f"[DEBUG] UserDonationHistoryView: CuentaComitente not found for user_id: {user_id}")
            return Transaccion.objects.none()
