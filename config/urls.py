from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from app.views.pages_view import (
    LoginPageView, CadastroPageView, DashboardPageView, TicketsPageView,
    DispositivosPageView, SalasPageView, EntidadesPageView,
    CategoriasPageView, ModelosPageView, UsuariosPageView, PermissoesPageView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth JWT
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API
    path('api/', include('app.urls')),

    # Pages
    path('login/', LoginPageView.as_view(), name='login'),
    path('cadastro/', CadastroPageView.as_view(), name='cadastro'),

    path('tickets/', TicketsPageView.as_view(), name='tickets'),
    path('dispositivos/', DispositivosPageView.as_view(), name='dispositivos'),
    path('salas/', SalasPageView.as_view(), name='salas'),
    path('entidades/', EntidadesPageView.as_view(), name='entidades'),
    path('categorias/', CategoriasPageView.as_view(), name='categorias'),
    path('modelos/', ModelosPageView.as_view(), name='modelos'),
    path('usuarios/', UsuariosPageView.as_view(), name='usuarios'),
    path('permissoes/', PermissoesPageView.as_view(), name='permissoes'),
    path('', DashboardPageView.as_view(), name='dashboard'),
]
