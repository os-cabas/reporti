from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from app.serializers.token import AdminTokenObtainSerializer

from app.views.auth_view import GoogleAuthView, MagicLinkSolicitarView, MagicLinkVerificarView
from app.views.dashboard_view import DashboardView
from app.views.pages_view import (
    LoginPageView, AcessoPageView, DashboardPageView, TicketsPageView,
    DispositivosPageView, SalasPageView, EntidadesPageView,
    CategoriasPageView, ModelosPageView, UsuariosPageView, PermissoesPageView,
    ManutencoesPageView, MeusReportesPageView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Auth JWT ──────────────────────────────────────────────────────────────
    path('api/auth/token/', TokenObtainPairView.as_view(serializer_class=AdminTokenObtainSerializer), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # ── RF001: Google OAuth ───────────────────────────────────────────────────
    path('api/auth/google/', GoogleAuthView.as_view(), name='auth_google'),

    # ── RF002: Magic Link ─────────────────────────────────────────────────────
    path('api/auth/magic-link/', MagicLinkSolicitarView.as_view(), name='magic_link_solicitar'),
    path('api/auth/magic-link/verificar/', MagicLinkVerificarView.as_view(), name='magic_link_verificar'),

    # ── RF015: Dashboard ──────────────────────────────────────────────────────
    path('api/dashboard/', DashboardView.as_view(), name='dashboard_api'),

    # ── API REST ──────────────────────────────────────────────────────────────
    path('api/', include('app.urls')),

    # ── Pages (templates) ─────────────────────────────────────────────────────
    path('login/', LoginPageView.as_view(), name='login'),
    path('acesso/', AcessoPageView.as_view(), name='acesso'),
    path('meus-reportes/', MeusReportesPageView.as_view(), name='meus_reportes'),
    path('tickets/', TicketsPageView.as_view(), name='tickets'),
    path('dispositivos/', DispositivosPageView.as_view(), name='dispositivos'),
    path('salas/', SalasPageView.as_view(), name='salas'),
    path('entidades/', EntidadesPageView.as_view(), name='entidades'),
    path('categorias/', CategoriasPageView.as_view(), name='categorias'),
    path('modelos/', ModelosPageView.as_view(), name='modelos'),
    path('usuarios/', UsuariosPageView.as_view(), name='usuarios'),
    path('permissoes/', PermissoesPageView.as_view(), name='permissoes'),
    path('manutencoes/', ManutencoesPageView.as_view(), name='manutencoes'),
    path('', DashboardPageView.as_view(), name='dashboard'),
]
