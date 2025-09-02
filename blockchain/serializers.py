from rest_framework import serializers
from .models import Cuadro

class CuadroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuadro
        fields = ['id', 'title', 'description', 'artist_wallet', 'total_tokens', 'artist_tokens', 'platform_tokens', 'investor_tokens', 'created_at']
        read_only_fields = ['artist_tokens', 'platform_tokens', 'investor_tokens', 'created_at']

    def create(self, validated_data):
        total_tokens = validated_data.get('total_tokens')
        
        # Lógica de distribución de tokens
        artist_share = 0.50
        platform_share = 0.10
        investor_share = 0.40
        
        validated_data['artist_tokens'] = int(total_tokens * artist_share)
        validated_data['platform_tokens'] = int(total_tokens * platform_share)
        validated_data['investor_tokens'] = int(total_tokens * investor_share)

        # Asegurarse de que la suma no exceda el total por redondeos
        current_total = validated_data['artist_tokens'] + validated_data['platform_tokens'] + validated_data['investor_tokens']
        remainder = total_tokens - current_total
        validated_data['investor_tokens'] += remainder # Añadir el remanente a los inversores

        return super().create(validated_data)
