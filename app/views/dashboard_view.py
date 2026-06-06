from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models.dispositivo import Dispositivo
from app.models.ticket import Ticket
from app.models.usuario import Usuario


class DashboardView(APIView):
    """
    RF015 – Dashboard com indicadores operacionais.
    Filtra pela entidade do usuário, exceto Administrador Geral.
    Usa aggregate() para executar uma única query de contagem de tickets
    e uma única query de contagem de dispositivos.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_global = user.perfil == 'admin_geral'

        # ── Dispositivos ─────────────────────────────────────────────────────
        disp_qs = Dispositivo.objects.all() if is_global else (
            Dispositivo.objects.filter(sala__entidade=user.entidade)
            if user.entidade_id else Dispositivo.objects.none()
        )

        disp_counts = disp_qs.aggregate(
            operacional=Count('id', filter=Q(situacao='operacional')),
            em_manutencao=Count('id', filter=Q(situacao='em_manutencao')),
        )

        # ── Tickets ──────────────────────────────────────────────────────────
        ticket_qs = Ticket.objects.all() if is_global else (
            Ticket.objects.filter(dispositivo__sala__entidade=user.entidade)
            if user.entidade_id else Ticket.objects.none()
        )

        ticket_counts = ticket_qs.aggregate(
            abertos=Count('id', filter=Q(status__in=['aberto', 'assumido', 'em_andamento'])),
            concluidos=Count('id', filter=Q(status__in=['resolvido', 'encerrado'])),
        )

        # ── Técnicos ativos (filtrado pela entidade) ─────────────────────────
        tecnicos_qs = Usuario.objects.filter(perfil='tecnico', is_active=True)
        if not is_global and user.entidade_id:
            tecnicos_qs = tecnicos_qs.filter(entidade=user.entidade)

        return Response({
            'equipamentos_ativos': disp_counts['operacional'],
            'equipamentos_em_manutencao': disp_counts['em_manutencao'],
            'chamados_abertos': ticket_counts['abertos'],
            'chamados_concluidos': ticket_counts['concluidos'],
            'tecnicos_ativos': tecnicos_qs.count(),
        })
