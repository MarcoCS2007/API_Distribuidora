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
