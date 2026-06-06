from rest_framework import permissions, viewsets
from app.models.sala import Sala
from app.permissions import EhTecnico
from app.serializers.sala import SalaSerializer


class SalaViewSet(viewsets.ModelViewSet):
    """
    RF007 – Cadastro de Salas.
    Técnicos e superiores podem criar/editar.
    Leitura filtrada pela entidade do usuário (RN005).
    """

    serializer_class = SalaSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Sala.objects.select_related('entidade').all()
        if user.entidade_id:
            return Sala.objects.select_related('entidade').filter(entidade=user.entidade)
        return Sala.objects.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EhTecnico()]
        return [permissions.IsAuthenticated()]
