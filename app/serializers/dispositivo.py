from rest_framework import serializers
from app.models.dispositivo import Dispositivo


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = [
            'id', 'codigo_qr', 'patrimonio', 'tipo', 'marca',
            'modelo', 'numero_serie', 'situacao', 'sala', 'criado_em',
        ]
        read_only_fields = ['criado_em']
