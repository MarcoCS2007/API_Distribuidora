from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsGestorVendasOrReadOnly(BasePermission):
    """
    Permite leitura para qualquer usuário autenticado.
    Escrita (PUT, PATCH, DELETE, POST) apenas para Admin ou Gestor de Vendas.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        if getattr(request.user, 'tipo', None) == 'GESTOR':
            try:
                # Agora o poder é do departamento de Vendas
                return request.user.perfil_gestor.departamento == 'VENDAS'
            except AttributeError:
                return False

        return False