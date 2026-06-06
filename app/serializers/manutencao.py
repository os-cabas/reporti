from rest_framework import serializers
from app.models.manutencao import Manutencao


class ManutencaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manutencao
        fields = [
            'id', 'dispositivo', 'tipo', 'descricao',
            'data_inicio', 'data_fim', 'tecnico', 'criado_em',
        ]
        read_only_fields = ['criado_em']

    def validate_tecnico(self, value):
        if value is None:
            raise serializers.ValidationError('Toda manutenção deve possuir técnico responsável.')
        return value
