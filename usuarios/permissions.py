from rest_framework.permissions import BasePermission

class PodeCadastrarUsuario(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Regras Específicas para Gestores
        if getattr(request.user, 'tipo', None) == 'GESTOR':
            tipo_solicitado = request.data.get('tipo')
            
            try:
                # O Django cria essa ligação (perfilgestor)
                departamento = request.user.perfil_gestor.departamento
            except AttributeError:
                return False # Bloqueia se houver falha de integridade no banco
            
            # Gestor de Logística pode criar outros Gestores
            if departamento == 'LOGISTICA' and tipo_solicitado == 'GESTOR':
                return True
                
            # Gestor de Vendas pode criar Representantes
            if departamento == 'VENDAS' and tipo_solicitado == 'REPRESENTANTE':
                return True

        return False

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsLogisticaOrReadOnly(BasePermission):
    """
    Permite leitura para qualquer usuário autenticado.
    Escrita (PUT, PATCH, DELETE) apenas para Admin ou Gestor de Logística.
    """
    def has_permission(self, request, view):
        # 1. Bloqueia quem não está logado
        if not request.user.is_authenticated:
            return False

        # 2. Se for uma requisição apenas de leitura, libera o acesso
        if request.method in SAFE_METHODS:
            return True

        # 3. Se for escrita/modificação, checa se é Admin
        if request.user.is_superuser:
            return True

        # 4. Checa se é Gestor de Logística
        if getattr(request.user, 'tipo', None) == 'GESTOR':
            try:
                return request.user.perfil_gestor.departamento == 'LOGISTICA'
            except AttributeError:
                return False

        # Se chegou aqui (ex: é Representante tentando dar DELETE), bloqueia
        return False