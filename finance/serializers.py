from rest_framework import serializers
from .models import Transaccion, CuentaComitente, TokenHolding
from decimal import Decimal

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

    class Meta:
        model = TokenHolding
        fields = ['token_id', 'quantity']

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
        fields = '__all__'
        read_only_fields = ('cuenta', 'estado', 'fecha')
