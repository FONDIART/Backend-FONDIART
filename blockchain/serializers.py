from rest_framework import serializers
from .models import CuadroToken

class CuadroTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuadroToken
        fields = '__all__'

class CuadroTokenDetailSerializer(serializers.ModelSerializer):
    artwork_title = serializers.CharField(source='artwork.title', read_only=True)
    FractionFrom = serializers.DecimalField(source='artwork.fractionFrom', max_digits=10, decimal_places=2, read_only=True)
    artwork_image = serializers.CharField(source='artwork.image.name', read_only=True)
    artwork_id = serializers.IntegerField(source='artwork.id', read_only=True)

    class Meta:
        model = CuadroToken
        fields = ['id', 'token_symbol', 'artwork_title', 'FractionFrom', 'artwork_image', 'artwork_id']

class TransferTokensSerializer(serializers.Serializer):
    """
    Serializer for validating token transfer requests.
    """
    contract_address = serializers.CharField(max_length=42)
    to_address = serializers.CharField(max_length=42)
    amount = serializers.IntegerField(min_value=1)

    def validate_contract_address(self, value):
        if not value.startswith('0x'):
            raise serializers.ValidationError("Address must start with 0x.")
        return value

    def validate_to_address(self, value):
        if not value.startswith('0x'):
            raise serializers.ValidationError("Address must start with 0x.")
        return value
