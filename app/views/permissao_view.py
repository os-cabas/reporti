from rest_framework import viewsets
from app.models.permissao import Permissao
from app.permissions import EhAdminEntidade
from app.serializers.permissao import PermissaoSerializer


class PermissaoViewSet(viewsets.ModelViewSet):
    """
    RF006 – Gerenciamento de Permissões.
    Apenas Administrador da Entidade ou Geral pode criar/editar permissões.
    """

    queryset = Permissao.objects.all()
    serializer_class = PermissaoSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EhAdminEntidade()]
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
