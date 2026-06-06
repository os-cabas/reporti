from rest_framework import serializers
from app.models.historico_dispositivo import HistoricoDispositivo


class HistoricoDispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoDispositivo
        fields = ['id', 'dispositivo', 'acao', 'descricao', 'usuario', 'criado_em']
        read_only_fields = ['criado_em']
