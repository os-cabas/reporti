from rest_framework import serializers
from app.models.historico_ticket import HistoricoTicket


class HistoricoTicketSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoTicket
        fields = ['id', 'ticket', 'acao', 'descricao', 'usuario', 'usuario_nome', 'criado_em']
        read_only_fields = ['criado_em']

    def get_usuario_nome(self, obj):
        if not obj.usuario:
            return None
        return obj.usuario.get_full_name() or obj.usuario.username


class ComentarioSerializer(serializers.Serializer):
    texto = serializers.CharField(max_length=2000)
