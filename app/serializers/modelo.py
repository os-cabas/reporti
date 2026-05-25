from rest_framework import serializers
from app.models.modelo import Modelo

class ModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modelo
        fields = ['id', 'nome', 'descricao', 'categoria']