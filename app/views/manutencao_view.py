from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models.historico_dispositivo import HistoricoDispositivo
from app.models.manutencao import Manutencao
from app.permissions import EhTecnico
from app.serializers.manutencao import ManutencaoSerializer


class ManutencaoViewSet(viewsets.ModelViewSet):
    """
    RF013 – Registro de Manutenção.
    RN008 – Toda manutenção deve possuir técnico responsável.
    """

    serializer_class = ManutencaoSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Manutencao.objects.select_related('dispositivo', 'tecnico').all()
        if user.entidade_id:
            return Manutencao.objects.select_related('dispositivo', 'tecnico').filter(
                dispositivo__sala__entidade=user.entidade
            )
        return Manutencao.objects.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EhTecnico()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def perform_create(self, serializer):
        manutencao = serializer.save()
        HistoricoDispositivo.objects.create(
            dispositivo=manutencao.dispositivo,
            acao='manutencao',
            descricao=f'Manutenção {manutencao.get_tipo_display()} registrada: {manutencao.descricao[:100]}',
            usuario=self.request.user,
        )

    @action(detail=False, methods=['get'], url_path='por-dispositivo/(?P<dispositivo_id>[^/.]+)')
    def por_dispositivo(self, request, dispositivo_id=None):
        qs = self.get_queryset().filter(dispositivo_id=dispositivo_id)
        return Response(ManutencaoSerializer(qs, many=True).data)
