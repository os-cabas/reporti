import uuid

from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models.dispositivo import Dispositivo
from app.models.historico_dispositivo import HistoricoDispositivo
from app.models.sala import Sala
from app.permissions import EhTecnico
from app.serializers.dispositivo import DispositivoSerializer
from app.serializers.historico_dispositivo import HistoricoDispositivoSerializer


class DispositivoViewSet(viewsets.ModelViewSet):
    """
    RF009 – Cadastro de Dispositivos.
    RF010 – Associação de Equipamentos a salas.
    RF011 – Alteração de Status (gera histórico – RN007).
    RF014 – Histórico de Equipamentos.
    """

    serializer_class = DispositivoSerializer

    def get_queryset(self):
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Dispositivo.objects.select_related('sala', 'modelo').all()
        if user.entidade_id:
            return Dispositivo.objects.select_related('sala', 'modelo').filter(
                sala__entidade=user.entidade
            )
        return Dispositivo.objects.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'alterar_status', 'mover'):
            return [EhTecnico()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def perform_create(self, serializer):
        # Salva com código temporário único para obter o pk
        dispositivo = serializer.save(codigo_qr=f"_INIT_{uuid.uuid4().hex[:10]}")
        # Gera o código definitivo: usa patrimônio se preenchido, senão usa o pk
        patrimonio = (dispositivo.patrimonio or '').strip()
        dispositivo.codigo_qr = patrimonio if patrimonio else f"DISP-{dispositivo.pk:06d}"
        dispositivo.save(update_fields=['codigo_qr'])
        HistoricoDispositivo.objects.create(
            dispositivo=dispositivo,
            acao='criacao',
            descricao='Dispositivo cadastrado no sistema.',
            usuario=self.request.user,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        dispositivo = serializer.save()
        HistoricoDispositivo.objects.create(
            dispositivo=dispositivo,
            acao='edicao',
            descricao='Dados do dispositivo atualizados.',
            usuario=self.request.user,
        )

    # ── RF011: alterar situação ──────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='alterar-status')
    @transaction.atomic
    def alterar_status(self, request, pk=None):  # noqa: ARG002
        dispositivo = self.get_object()
        nova_situacao = request.data.get('situacao', '').strip()
        situacoes_validas = [s[0] for s in Dispositivo.SITUACOES]

        if nova_situacao not in situacoes_validas:
            return Response(
                {'erro': f'Situação inválida. Opções: {situacoes_validas}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        situacao_anterior = dispositivo.get_situacao_display()
        dispositivo.situacao = nova_situacao
        dispositivo.save(update_fields=['situacao'])

        HistoricoDispositivo.objects.create(
            dispositivo=dispositivo,
            acao='status',
            descricao=f'Situação alterada de "{situacao_anterior}" para "{dispositivo.get_situacao_display()}".',
            usuario=request.user,
        )

        return Response(DispositivoSerializer(dispositivo).data)

    # ── RF010: mover para outra sala ─────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='mover')
    @transaction.atomic
    def mover(self, request, pk=None):  # noqa: ARG002
        dispositivo = self.get_object()
        sala_id = request.data.get('sala_id')

        try:
            sala = Sala.objects.get(pk=sala_id)
        except Sala.DoesNotExist:
            return Response({'erro': 'Sala não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        sala_anterior = str(dispositivo.sala) if dispositivo.sala else 'sem sala'
        dispositivo.sala = sala
        dispositivo.save(update_fields=['sala'])

        HistoricoDispositivo.objects.create(
            dispositivo=dispositivo,
            acao='localizacao',
            descricao=f'Movido de "{sala_anterior}" para "{sala}".',
            usuario=request.user,
        )

        return Response(DispositivoSerializer(dispositivo).data)

    # ── RF014: histórico completo ────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):  # noqa: ARG002
        dispositivo = self.get_object()
        qs = dispositivo.historico.select_related('usuario').all()
        return Response(HistoricoDispositivoSerializer(qs, many=True).data)

    # ── RF009 / RN001: buscar por código QR (acesso de qualquer perfil) ──────

    @action(detail=False, methods=['get'], url_path='buscar',
            permission_classes=[permissions.IsAuthenticated])
    def buscar(self, request):
        codigo = request.query_params.get('q', '').strip()
        if not codigo:
            return Response({'erro': 'Parâmetro q é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            d = Dispositivo.objects.select_related('sala', 'modelo').get(codigo_qr=codigo)
        except Dispositivo.DoesNotExist:
            return Response({'erro': 'Equipamento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'id': d.pk,
            'codigo_qr': d.codigo_qr,
            'tipo': d.tipo,
            'marca': d.marca,
            'situacao': d.situacao,
            'situacao_display': d.get_situacao_display(),
            'sala': str(d.sala) if d.sala else None,
            'modelo': str(d.modelo) if d.modelo else None,
        })
