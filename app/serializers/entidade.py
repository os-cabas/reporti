from rest_framework import serializers
from app.models.entidade import Entidade


class EntidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entidade
        fields = ['id', 'nome', 'tipo', 'email_responsavel', 'descricao', 'status', 'criado_em']
        read_only_fields = ['criado_em']
