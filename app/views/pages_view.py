from django.views.generic import TemplateView


class LoginPageView(TemplateView):
    template_name = 'login.html'


class DashboardPageView(TemplateView):
    template_name = 'dashboard.html'


class TicketsPageView(TemplateView):
    template_name = 'tickets.html'


class DispositivosPageView(TemplateView):
    template_name = 'dispositivos.html'


class SalasPageView(TemplateView):
    template_name = 'salas.html'
