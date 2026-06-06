from rest_framework import viewsets
from app.models.categoria import Categoria
from app.serializers.categoria import CategoriaSerializer

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer