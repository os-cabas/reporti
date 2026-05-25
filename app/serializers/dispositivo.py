from rest_framework import serializers
from app.models.dispositivo import Dispositivo

class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ['id', 'sala', 'modelo']