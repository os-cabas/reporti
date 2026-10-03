import re

from rest_framework import serializers
from app.models.ticket import Ticket

# Quebras de linha e caracteres de controle não cabem em um título:
# ele vira assunto de e-mail e célula de CSV.
_CARACTERES_DE_CONTROLE = re.compile(r'[\x00-\x1f\x7f]')


class TicketSerializer(serializers.ModelSerializer):
    descricao = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    class Meta:
        model = Ticket
        fields = [
            'id', 'titulo', 'descricao', 'status', 'prioridade', 'tipo_problema',
            'usuario', 'tecnico', 'dispositivo',
            'criado_em', 'atualizado_em',
        ]
        # status e tecnico só mudam pelas ações de atendimento (que geram histórico);
        # usuario é sempre quem abriu o chamado.
        read_only_fields = ['status', 'usuario', 'tecnico', 'criado_em', 'atualizado_em']

    def validate_titulo(self, value):
        if _CARACTERES_DE_CONTROLE.search(value):
            raise serializers.ValidationError(
                'O título não pode conter quebras de linha ou caracteres de controle.'
            )
        return value
