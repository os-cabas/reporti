from rest_framework import permissions, viewsets
from app.models.usuario import Usuario
from app.permissions import EhAdminEntidade
from app.serializers.usuario import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    RF004 – Cadastro de Usuários.
    RF005 – Gerenciamento de Técnicos.
    Administrador da Entidade gerencia usuários da própria entidade (RN005).
    """

    serializer_class = UsuarioSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Usuario.objects.all()
        if user.perfil == 'admin_entidade' and user.entidade_id:
            return Usuario.objects.filter(entidade=user.entidade)
        return Usuario.objects.filter(pk=user.pk)

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [EhAdminEntidade()]
        return [permissions.IsAuthenticated()]
