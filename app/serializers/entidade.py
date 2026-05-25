from rest_framework import serializers
from app.models.entidade import Entidade

class EntidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entidade
        fields = ['id', 'nome']