from django.db.models import Count, Min, Q
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models.dispositivo import Dispositivo
from app.models.ticket import Ticket
from app.models.usuario import Usuario
from app.permissions import EhTecnico


def _media_minutos(intervalos):
    """Média em minutos de uma lista de timedelta, ou None se a lista for vazia."""
    if not intervalos:
        return None
    total = sum(i.total_seconds() for i in intervalos)
    return round(total / len(intervalos) / 60, 1)


class DashboardView(APIView):
    """
    RF015 – Dashboard com indicadores operacionais.
    Filtra pela entidade do usuário, exceto Administrador Geral.
    Restrito a técnicos e administradores: os indicadores expõem chamados de
    outros usuários, que o Usuário Comum não pode ver.
    Todas as contagens vêm de aggregate() no banco, sem depender da paginação.
    """

    permission_classes = [EhTecnico]

    def get(self, request):
        user = request.user
        is_global = user.perfil == 'admin_geral'

        # ── Dispositivos ─────────────────────────────────────────────────────
        disp_qs = Dispositivo.objects.all() if is_global else (
            Dispositivo.objects.filter(sala__entidade=user.entidade)
            if user.entidade_id else Dispositivo.objects.none()
        )

        disp_counts = disp_qs.aggregate(
            total=Count('id'),
            operacional=Count('id', filter=Q(situacao='operacional')),
            em_manutencao=Count('id', filter=Q(situacao='em_manutencao')),
            inativos=Count('id', filter=Q(situacao__in=['inativo', 'descartado'])),
        )

        # ── Tickets ──────────────────────────────────────────────────────────
        ticket_qs = Ticket.objects.all() if is_global else (
            Ticket.objects.filter(dispositivo__sala__entidade=user.entidade)
            if user.entidade_id else Ticket.objects.none()
        )

        ticket_counts = ticket_qs.aggregate(
            abertos=Count('id', filter=Q(status__in=Ticket.STATUS_PENDENTES)),
            aguardando=Count('id', filter=Q(status='aberto')),
            em_andamento=Count('id', filter=Q(status__in=['assumido', 'em_andamento'])),
            concluidos=Count('id', filter=Q(status__in=['resolvido', 'encerrado'])),
        )

        # ── Tempo médio de atendimento (datas vêm do histórico do chamado) ───
        marcos = ticket_qs.annotate(
            assumido_em=Min('historico__criado_em', filter=Q(historico__acao='assumido')),
            resolvido_em=Min('historico__criado_em', filter=Q(historico__acao='resolvido')),
        ).values_list('criado_em', 'assumido_em', 'resolvido_em')

        ate_assumir, ate_resolver = [], []
        for criado_em, assumido_em, resolvido_em in marcos:
            if assumido_em and assumido_em >= criado_em:
                ate_assumir.append(assumido_em - criado_em)
            if resolvido_em and resolvido_em >= criado_em:
                ate_resolver.append(resolvido_em - criado_em)

        # ── Cortes por prioridade e tipo de problema ─────────────────────────
        pendentes_qs = ticket_qs.filter(status__in=Ticket.STATUS_PENDENTES)
        por_prioridade = dict(
            pendentes_qs.order_by().values_list('prioridade').annotate(total=Count('id'))
        )
        por_tipo = dict(
            ticket_qs.order_by().values_list('tipo_problema').annotate(total=Count('id'))
        )

        # ── Ranking: onde concentrar a manutenção preventiva ─────────────────
        com_disp = ticket_qs.filter(dispositivo__isnull=False).order_by()
        pendentes = Count('id', filter=Q(status__in=Ticket.STATUS_PENDENTES))

        top_dispositivos = [
            {
                'id': linha['dispositivo'],
                'codigo_qr': linha['dispositivo__codigo_qr'],
                'nome': f"{linha['dispositivo__tipo']} {linha['dispositivo__marca']}".strip(),
                'sala': linha['dispositivo__sala__nome'],
                'total': linha['total'],
                'pendentes': linha['pendentes'],
            }
            for linha in com_disp.values(
                'dispositivo', 'dispositivo__codigo_qr', 'dispositivo__tipo',
                'dispositivo__marca', 'dispositivo__sala__nome',
            ).annotate(total=Count('id'), pendentes=pendentes).order_by('-total', 'dispositivo')[:5]
        ]

        top_salas = [
            {
                'id': linha['dispositivo__sala'],
                'nome': linha['dispositivo__sala__nome'],
                'bloco': linha['dispositivo__sala__bloco'],
                'total': linha['total'],
                'pendentes': linha['pendentes'],
            }
            for linha in com_disp.filter(dispositivo__sala__isnull=False).values(
                'dispositivo__sala', 'dispositivo__sala__nome', 'dispositivo__sala__bloco',
            ).annotate(total=Count('id'), pendentes=pendentes).order_by('-total', 'dispositivo__sala')[:5]
        ]

        # ── Atividade recente ────────────────────────────────────────────────
        recentes = [
            {
                'id': t.pk,
                'titulo': t.titulo,
                'status': t.status,
                'prioridade': t.prioridade,
                'criado_em': t.criado_em,
                'dispositivo': f'{t.dispositivo.tipo} {t.dispositivo.marca}'.strip() if t.dispositivo else None,
            }
            for t in ticket_qs.select_related('dispositivo').order_by('-criado_em', '-id')[:10]
        ]

        # ── Técnicos ativos (filtrado pela entidade) ─────────────────────────
        tecnicos_qs = Usuario.objects.filter(perfil='tecnico', is_active=True)
        if not is_global:
            tecnicos_qs = (
                tecnicos_qs.filter(entidade=user.entidade) if user.entidade_id else tecnicos_qs.none()
            )

        return Response({
            'equipamentos_total': disp_counts['total'],
            'equipamentos_ativos': disp_counts['operacional'],
            'equipamentos_em_manutencao': disp_counts['em_manutencao'],
            'equipamentos_inativos': disp_counts['inativos'],
            'chamados_abertos': ticket_counts['abertos'],
            'chamados_aguardando': ticket_counts['aguardando'],
            'chamados_em_andamento': ticket_counts['em_andamento'],
            'chamados_concluidos': ticket_counts['concluidos'],
            'tecnicos_ativos': tecnicos_qs.count(),
            'tempo_medio_assumir_min': _media_minutos(ate_assumir),
            'tempo_medio_resolver_min': _media_minutos(ate_resolver),
            'chamados_medidos_assumir': len(ate_assumir),
            'chamados_medidos_resolver': len(ate_resolver),
            'pendentes_por_prioridade': {chave: por_prioridade.get(chave, 0) for chave, _ in Ticket.PRIORIDADES},
            'chamados_por_tipo': {chave: por_tipo.get(chave, 0) for chave, _ in Ticket.TIPOS_PROBLEMA},
            'top_dispositivos': top_dispositivos,
            'top_salas': top_salas,
            'recentes': recentes,
        })
