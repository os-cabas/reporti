from rest_framework import viewsets
from app.models.usuario_permissao import UsuarioPermissao
from app.serializers.usuario_permissao import UsuarioPermissaoSerializer

class UsuarioPermissaoViewSet(viewsets.ModelViewSet):
    queryset = UsuarioPermissao.objects.select_related('usuario', 'permissao').all()
    serializer_class = UsuarioPermissaoSerializer