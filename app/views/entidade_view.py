from rest_framework import viewsets
from app.models.entidade import Entidade
from app.serializers.entidade import EntidadeSerializer

class EntidadeViewSet(viewsets.ModelViewSet):
    queryset = Entidade.objects.all()
    serializer_class = EntidadeSerializer