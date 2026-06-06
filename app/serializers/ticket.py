from rest_framework import serializers
from app.models.ticket import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'id', 'titulo', 'descricao', 'status',
            'usuario', 'tecnico', 'dispositivo',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']

