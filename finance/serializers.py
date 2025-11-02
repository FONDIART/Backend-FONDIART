from rest_framework import serializers
from .models import Transaccion, CuentaComitente, TokenHolding, Donation, SellOrder
from decimal import Decimal

class ProjectDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['id', 'project', 'donor', 'amount', 'timestamp']
        read_only_fields = ('donor', 'timestamp')

class DonationSerializer(serializers.Serializer):
    artist_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('1.00'))

class FundProjectSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('1.00'))

class BuyTokensSerializer(serializers.Serializer):
    artwork_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class TokenHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenHolding
        fields = '__all__'

class UserTokenHoldingSerializer(serializers.ModelSerializer):
    token_id = serializers.IntegerField(source='token.id', read_only=True)
    token_name = serializers.CharField(source='token.token_name', read_only=True)
    unit_price = serializers.DecimalField(source='token.artwork.fractionFrom', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = TokenHolding
        fields = ['token_id', 'token_name', 'quantity', 'unit_price']

class CuentaComitenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaComitente
        fields = '__all__'

class CuentaComitenteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaComitente
        fields = ['balance']

class TransaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaccion
        fields = ['id', 'cuenta', 'tipo', 'artwork', 'cantidad_tokens', 'monto_pesos', 'fecha', 'estado']
        read_only_fields = ('cuenta', 'estado', 'fecha')

class CheckFundsSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class LiquidateArtworkSerializer(serializers.Serializer):
    artwork_id = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class SellOrderSerializer(serializers.ModelSerializer):
    token_symbol = serializers.CharField(source='token.token_symbol', read_only=True)
    token_name = serializers.CharField(source='token.token_name', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = SellOrder
        fields = [
            'id', 'token', 'token_symbol', 'token_name', 'user', 'user_name', 
            'quantity', 'price', 'publication_date', 'status'
        ]
        read_only_fields = ('user', 'publication_date')

class BuyFromSellOrderSerializer(serializers.Serializer):
    sell_order_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class DonationTransactionSerializer(TransaccionSerializer):
    artist_name = serializers.SerializerMethodField()
    
    class Meta(TransaccionSerializer.Meta):
        fields = ['monto_pesos', 'artist_name', 'fecha']

    def get_artist_name(self, obj):
        if obj.recipient_artist:
            return obj.recipient_artist.name
        if obj.artwork and obj.artwork.artist:
            return obj.artwork.artist.name
        return None
class DonationHistorySerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)
    artist_name = serializers.CharField(source='project.artist.name', read_only=True)

    class Meta:
        model = Donation
        fields = ['id', 'project', 'project_title', 'artist_name', 'amount', 'timestamp']
