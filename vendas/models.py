from django.db import models
from core.models import BaseModel
from usuarios.models import PerfilRepresentante
from catalogo.models import Produto

class Pedido(BaseModel):
    STATUS_CHOICES = [
        ('EM_DIGITACAO', 'Em Digitação'), # Representante montando o pedido/rascunho
        ('FINALIZADO', 'Finalizado'),     # Pedido fechado e pronto para envio/faturamento
        ('CANCELADO', 'Cancelado'),       # Representante desistiu
    ]

    representante = models.ForeignKey(
        PerfilRepresentante, 
        on_delete=models.PROTECT, # Impede apagar o representante se ele tiver vendas
        related_name='pedidos'
    )
    
    cliente_nome = models.CharField(max_length=200)
    cliente_cnpj = models.CharField(max_length=18)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EM_DIGITACAO')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente_nome} ({self.get_status_display()})"


class ItemPedido(BaseModel):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, # Se apagar o pedido (rascunho), os itens somem
        related_name='itens'
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.PROTECT, # Impede apagar o produto do catálogo se ele já foi vendido
        related_name='historico_vendas'
    )
    
    quantidade = models.PositiveIntegerField()
    preco_unitario_aplicado = models.DecimalField(max_digits=10, decimal_places=2) 
    desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Pedido {self.pedido.id})"