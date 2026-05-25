from rest_framework import viewsets
from app.models.dispositivo import Dispositivo
from app.serializers.dispositivo import DispositivoSerializer

class DispositivoViewSet(viewsets.ModelViewSet):
    queryset = Dispositivo.objects.select_related('sala', 'modelo').all()
    serializer_class = DispositivoSerializer
