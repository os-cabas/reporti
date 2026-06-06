from rest_framework import serializers
from app.models.sala import Sala


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ['id', 'nome', 'bloco', 'andar', 'numero', 'observacao', 'entidade']
