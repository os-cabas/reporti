from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, PermissaoViewSet, UsuarioPermissaoViewSet,
    EntidadeViewSet, SalaViewSet, CategoriaViewSet,
    ModeloViewSet, DispositivoViewSet, TicketViewSet,
)

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet, basename='usuarios')
router.register('permissoes', PermissaoViewSet, basename='permissoes')
router.register('usuario-permissoes', UsuarioPermissaoViewSet, basename='usuario-permissoes')
router.register('entidades', EntidadeViewSet, basename='entidades')
router.register('salas', SalaViewSet, basename='salas')
router.register('categorias', CategoriaViewSet, basename='categorias')
router.register('modelos', ModeloViewSet, basename='modelos')
router.register('dispositivos', DispositivoViewSet, basename='dispositivos')
router.register('tickets', TicketViewSet, basename='tickets')

urlpatterns = router.urls
