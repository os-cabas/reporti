from rest_framework import permissions, viewsets
from app.models.entidade import Entidade
from app.permissions import EhAdminEntidade, EhAdminGeral
from app.serializers.entidade import EntidadeSerializer


class EntidadeViewSet(viewsets.ModelViewSet):
    """
    RF003 – Cadastro de Entidade.
    Criação e exclusão: somente Administrador Geral (RN006).
    Edição: Administrador da Entidade ou Geral.
    Leitura: qualquer usuário autenticado (filtrado pela própria entidade).
    """

    serializer_class = EntidadeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Entidade.objects.all()
        if user.entidade_id:
            return Entidade.objects.filter(pk=user.entidade_id)
        return Entidade.objects.none()

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [EhAdminGeral()]
        if self.action in ('update', 'partial_update'):
            return [EhAdminEntidade()]
        return [permissions.IsAuthenticated()]
