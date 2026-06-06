from rest_framework import serializers
from app.models.historico_ticket import HistoricoTicket


class HistoricoTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoTicket
        fields = ['id', 'ticket', 'acao', 'descricao', 'usuario', 'criado_em']
        read_only_fields = ['criado_em']
