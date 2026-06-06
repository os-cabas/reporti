from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from app.models.historico_ticket import HistoricoTicket
from app.models.ticket import Ticket
from app.permissions import EhTecnico
from app.serializers.historico_ticket import HistoricoTicketSerializer
from app.serializers.ticket import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    """
    RF012 – Atendimento de Chamados.
    RN004 – Ticket encerrado não pode ser editado (verificado em get_object).
    """

    serializer_class = TicketSerializer

    # ── Queryset filtrado por perfil ─────────────────────────────────────────

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Ticket.objects.select_related('usuario', 'tecnico', 'dispositivo').all()
        if user.perfil in ('tecnico', 'admin_entidade') and user.entidade_id:
            return (
                Ticket.objects.filter(dispositivo__sala__entidade=user.entidade)
                | Ticket.objects.filter(usuario=user)
            ).select_related('usuario', 'tecnico', 'dispositivo').distinct()
        return Ticket.objects.filter(usuario=user).select_related('dispositivo')

    # ── Permissões por ação ──────────────────────────────────────────────────

    def get_permissions(self):
        acoes_tecnico = {'update', 'partial_update', 'destroy',
                         'assumir', 'atualizar_status', 'resolver', 'encerrar'}
        if self.action in acoes_tecnico:
            return [EhTecnico()]
        return [permissions.IsAuthenticated()]

    # ── RN004: bloqueia qualquer escrita em ticket encerrado ─────────────────

    def get_object(self):
        ticket = super().get_object()
        acoes_escrita = {'assumir', 'atualizar_status', 'resolver', 'encerrar',
                         'update', 'partial_update', 'destroy'}
        if self.action in acoes_escrita and ticket.status == 'encerrado':
            raise PermissionDenied('Ticket encerrado não pode ser editado.')
        return ticket

    # ── Criação ──────────────────────────────────────────────────────────────

    @transaction.atomic
    def perform_create(self, serializer):
        ticket = serializer.save(usuario=self.request.user)
        HistoricoTicket.objects.create(
            ticket=ticket, acao='aberto',
            descricao='Chamado aberto.', usuario=self.request.user,
        )

    # ── Helper interno: muda status e registra histórico numa transação ──────

    def _mudar_status(self, ticket, novo_status, descricao, usuario, tecnico=None):
        fields = ['status']
        ticket.status = novo_status
        if tecnico is not None:
            ticket.tecnico = tecnico
            fields.append('tecnico')
        ticket.save(update_fields=fields)
        HistoricoTicket.objects.create(
            ticket=ticket, acao=novo_status, descricao=descricao, usuario=usuario,
        )

    # ── RF012: ações de atendimento ──────────────────────────────────────────

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def assumir(self, request, pk=None):  # noqa: ARG002
        ticket = self.get_object()
        nome = request.user.get_full_name() or request.user.username
        self._mudar_status(ticket, 'assumido', f'Assumido por {nome}.', request.user, tecnico=request.user)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='atualizar-status')
    @transaction.atomic
    def atualizar_status(self, request, pk=None):  # noqa: ARG002
        ticket = self.get_object()
        novo_status = request.data.get('status', '').strip()
        status_validos = [s[0] for s in Ticket.STATUS if s[0] != 'encerrado']
        if novo_status not in status_validos:
            return Response(
                {'erro': f'Status inválido. Opções: {status_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        anterior = ticket.get_status_display()
        novo_display = dict(Ticket.STATUS).get(novo_status, novo_status)
        self._mudar_status(
            ticket, novo_status,
            f'Status alterado de "{anterior}" para "{novo_display}".',
            request.user,
        )
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def resolver(self, request, pk=None):  # noqa: ARG002
        ticket = self.get_object()
        descricao = request.data.get('descricao', 'Chamado marcado como resolvido.')
        self._mudar_status(ticket, 'resolvido', descricao, request.user)
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def encerrar(self, request, pk=None):  # noqa: ARG002
        ticket = self.get_object()
        descricao = request.data.get('descricao', 'Chamado encerrado.')
        self._mudar_status(ticket, 'encerrado', descricao, request.user)
        return Response(TicketSerializer(ticket).data)

    # ── Histórico do ticket ──────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):  # noqa: ARG002
        ticket = self.get_object()
        qs = ticket.historico.select_related('usuario').all()
        return Response(HistoricoTicketSerializer(qs, many=True).data)
