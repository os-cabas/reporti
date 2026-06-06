from rest_framework import permissions, viewsets
from app.models.usuario_permissao import UsuarioPermissao
from app.permissions import EhAdminEntidade
from app.serializers.usuario_permissao import UsuarioPermissaoSerializer


class UsuarioPermissaoViewSet(viewsets.ModelViewSet):
    """
    RF006 – Atribuição de permissões específicas a técnicos.
    Apenas Administrador da Entidade ou Geral pode gerenciar.
    """

    serializer_class = UsuarioPermissaoSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return UsuarioPermissao.objects.select_related('usuario', 'permissao').all()
        if user.entidade_id:
            return UsuarioPermissao.objects.select_related('usuario', 'permissao').filter(
                usuario__entidade=user.entidade
            )
        return UsuarioPermissao.objects.filter(usuario=user).select_related('permissao')

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [EhAdminEntidade()]
        return [permissions.IsAuthenticated()]
