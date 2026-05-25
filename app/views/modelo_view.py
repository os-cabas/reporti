from rest_framework import viewsets
from app.models.modelo import Modelo
from app.serializers.modelo import ModeloSerializer

class ModeloViewSet(viewsets.ModelViewSet):
    queryset = Modelo.objects.select_related('categoria').all()
    serializer_class = ModeloSerializer