from rest_framework import viewsets
from .models import Pedido
from .serializers import PedidoSerializer
from .permissions import AcessoVendas

class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [AcessoVendas]

    def get_queryset(self):
        user = self.request.user
        
        # Filtro de segurança primário (IDOR em listagens)
        if not user.is_authenticated:
            return Pedido.objects.none()
            
        qs = Pedido.objects.all().order_by('-criado_em')
        
        if user.is_superuser:
            return qs
            
        tipo = getattr(user, 'tipo', None)
        
        if tipo == 'REPRESENTANTE':
            # Retorna apenas a carteira de pedidos do próprio representante
            return qs.filter(representante__usuario=user)
            
        if tipo == 'GESTOR':
            if hasattr(user, 'perfil_gestor') and user.perfil_gestor.departamento == 'LOGISTICA':
                return qs.filter(status='FINALIZADO')
            # Vendas vê o panorama geral
            return qs 
            
        return Pedido.objects.none()

    # Sobrescreve o DELETE para que atue como Cancelamento em vez de exclusão física
    def perform_destroy(self, instance):
        instance.status = 'CANCELADO'
        instance.save()