from rest_framework import viewsets
from app.models.sala import Sala
from app.serializers.sala import SalaSerializer

class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.select_related('entidade').all()
    serializer_class = SalaSerializer