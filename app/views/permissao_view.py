from rest_framework import viewsets
from app.models.permissao import Permissao
from app.serializers.permissao import PermissaoSerializer

class PermissaoViewSet(viewsets.ModelViewSet):
    queryset = Permissao.objects.all()
    serializer_class = PermissaoSerializer