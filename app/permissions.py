from rest_framework import permissions


class EhAdminGeral(permissions.BasePermission):
    """Somente Administrador Geral."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.perfil == 'admin_geral'
        )


class EhAdminEntidade(permissions.BasePermission):
    """Administrador da Entidade ou Administrador Geral."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.perfil in ('admin_entidade', 'admin_geral')
        )


class EhTecnico(permissions.BasePermission):
    """Técnico, Administrador da Entidade ou Administrador Geral."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.perfil in ('tecnico', 'admin_entidade', 'admin_geral')
        )
