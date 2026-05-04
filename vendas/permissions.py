from rest_framework.permissions import BasePermission, SAFE_METHODS

class AcessoVendas(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin tem acesso total
        if request.user.is_superuser:
            return True
            
        tipo = getattr(request.user, 'tipo', None)
        
        if tipo == 'REPRESENTANTE':
            # Bloqueia se o pedido for de outro representante
            if obj.representante.usuario != request.user:
                return False
                
            # Bloqueia alteração/deleção de pedidos que não sejam rascunhos (EM_DIGITACAO)
            if request.method not in SAFE_METHODS and obj.status != 'EM_DIGITACAO':
                return False
            return True
            
        if tipo == 'GESTOR':
            # Gestores têm acesso apenas de leitura (GET) aos pedidos no MVP
            if request.method in SAFE_METHODS:
                if request.user.perfil_gestor.departamento == 'LOGISTICA':
                    # Logística só enxerga pedidos prontos para envio
                    return obj.status == 'FINALIZADO'
                # Gestor de Vendas vê tudo
                return True 
                
        return False