from rest_framework import serializers
from .models import Transaccion, CuentaComitente

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
