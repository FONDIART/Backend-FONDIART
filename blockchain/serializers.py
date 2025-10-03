from rest_framework import serializers
from .models import CuadroToken

class CuadroTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuadroToken
        fields = '__all__'