import base64
import io
import logging
import uuid

import qrcode
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.exportacao import data_local, resposta_csv
from app.models.dispositivo import Dispositivo
from app.models.historico_dispositivo import HistoricoDispositivo
from app.models.sala import Sala
from app.models.ticket import Ticket
from app.permissions import EhAdminEntidade, EhTecnico
from app.serializers.dispositivo import DispositivoSerializer
from app.serializers.historico_dispositivo import HistoricoDispositivoSerializer

logger = logging.getLogger('app.dispositivos')

# Teto de etiquetas por requisição: cada QR Code é gerado em memória.
MAX_ETIQUETAS_POR_LOTE = 200


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
        if self.action in ('create', 'update', 'partial_update', 'destroy',
                           'alterar_status', 'mover', 'qr_lote'):
            return [EhTecnico()]
        if self.action == 'exportar':
            return [EhAdminEntidade()]
        return [permissions.IsAuthenticated()]

    def _salas_visiveis(self):
        """Salas que o usuário pode usar: as da própria entidade (RN005)."""
        user = self.request.user
        if user.perfil == 'admin_geral':
            return Sala.objects.all()
        if user.entidade_id:
            return Sala.objects.filter(entidade=user.entidade)
        return Sala.objects.none()

    def _qr_data_uri(self, codigo):
        scan_url = f"{self.request.scheme}://{self.request.get_host()}/r/{codigo}/"
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(scan_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f'data:image/png;base64,{b64}', scan_url

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
        nova_situacao = str(request.data.get('situacao', '')).strip()
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
            sala = self._salas_visiveis().get(pk=sala_id)
        except (Sala.DoesNotExist, ValueError, TypeError):
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

    # ── Geração de imagem QR Code ────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='qr-image',
            permission_classes=[permissions.IsAuthenticated])
    def qr_image(self, request):
        codigo = request.query_params.get('codigo', '').strip()
        if not codigo:
            return Response({'erro': 'Parâmetro codigo é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(codigo) > 100:
            return Response({'erro': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        image, scan_url = self._qr_data_uri(codigo)
        return Response({'image': image, 'url': scan_url})

    # ── Etiquetas QR de uma sala inteira, para impressão em lote ─────────────

    @action(detail=False, methods=['get'], url_path='qr-lote')
    def qr_lote(self, request):
        try:
            sala = self._salas_visiveis().get(pk=request.query_params.get('sala'))
        except (Sala.DoesNotExist, ValueError, TypeError):
            return Response({'erro': 'Sala não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        dispositivos = list(
            self.get_queryset()
            .filter(sala=sala)
            .exclude(situacao='descartado')
            .order_by('codigo_qr')[:MAX_ETIQUETAS_POR_LOTE + 1]
        )
        truncado = len(dispositivos) > MAX_ETIQUETAS_POR_LOTE

        etiquetas = [
            {
                'id': d.pk,
                'codigo_qr': d.codigo_qr,
                'nome': f'{d.tipo} {d.marca}'.strip(),
                'image': self._qr_data_uri(d.codigo_qr)[0],
            }
            for d in dispositivos[:MAX_ETIQUETAS_POR_LOTE]
        ]
        return Response({
            'sala': sala.nome,
            'bloco': sala.bloco,
            'truncado': truncado,
            'etiquetas': etiquetas,
        })

    # ── Inventário em CSV (Administrador da Entidade ou Geral) ───────────────

    @action(detail=False, methods=['get'])
    def exportar(self, request):
        linhas = [
            (
                d.pk, d.codigo_qr, d.patrimonio, d.tipo, d.marca,
                d.modelo.nome if d.modelo else '',
                d.numero_serie, d.get_situacao_display(),
                d.sala.nome if d.sala else '',
                d.sala.bloco if d.sala else '',
                data_local(d.criado_em),
            )
            for d in self.get_queryset().order_by('pk')
        ]
        logger.info('Exportação de %d dispositivos pelo usuário #%s', len(linhas), request.user.pk)
        return resposta_csv(
            'dispositivos',
            ['ID', 'Código QR', 'Patrimônio', 'Tipo', 'Marca', 'Modelo',
             'Nº de série', 'Situação', 'Sala', 'Bloco', 'Cadastrado em'],
            linhas,
        )

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
            # Só a contagem: os chamados de outros usuários não são expostos.
            'chamados_abertos': Ticket.objects.filter(
                dispositivo=d, status__in=Ticket.STATUS_PENDENTES,
            ).count(),
        })
