from django.conf import settings
from django.views.generic import TemplateView

from app.models.dispositivo import Dispositivo


class LoginPageView(TemplateView):
    template_name = 'login.html'


class AcessoPageView(TemplateView):
    template_name = 'acesso.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['google_client_id'] = settings.GOOGLE_CLIENT_ID
        return ctx


class DashboardPageView(TemplateView):
    template_name = 'dashboard.html'


class TicketsPageView(TemplateView):
    template_name = 'tickets.html'


class DispositivosPageView(TemplateView):
    template_name = 'dispositivos.html'


class SalasPageView(TemplateView):
    template_name = 'salas.html'


class EntidadesPageView(TemplateView):
    template_name = 'entidades.html'


class CategoriasPageView(TemplateView):
    template_name = 'categorias.html'


class ModelosPageView(TemplateView):
    template_name = 'modelos.html'


class UsuariosPageView(TemplateView):
    template_name = 'usuarios.html'


class PermissoesPageView(TemplateView):
    template_name = 'permissoes.html'


class ManutencoesPageView(TemplateView):
    template_name = 'manutencoes.html'


class MeusReportesPageView(TemplateView):
    template_name = 'meus-reportes.html'


class ReportarDispositivoPageView(TemplateView):
    template_name = 'reportar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        codigo = kwargs.get('codigo_qr', '')
        try:
            d = Dispositivo.objects.select_related('sala', 'modelo').get(codigo_qr=codigo)
            ctx['dispositivo'] = {
                'id': d.pk,
                'codigo_qr': d.codigo_qr,
                'tipo': d.tipo,
                'marca': d.marca,
                'situacao': d.get_situacao_display(),
                'sala': str(d.sala) if d.sala else None,
                'modelo': str(d.modelo) if d.modelo else None,
            }
        except Dispositivo.DoesNotExist:
            ctx['dispositivo'] = None
        ctx['codigo_qr'] = codigo
        return ctx
