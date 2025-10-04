from rest_framework import serializers
from .models import CuadroToken

class CuadroTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuadroToken
        fields = '__all__'

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

