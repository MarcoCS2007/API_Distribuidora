from rest_framework import serializers
from django.db import transaction
from .models import Pedido, ItemPedido
from catalogo.models import Produto

class ItemPedidoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.ReadOnlyField(source='produto.nome')
    
    class Meta:
        model = ItemPedido
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade', 
            'preco_unitario_aplicado', 'desconto_percentual', 'subtotal'
        ]
        # Backend assume a matemática. Frontend não envia preço nem subtotal.
        read_only_fields = ['preco_unitario_aplicado', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True)
    representante_nome = serializers.ReadOnlyField(source='representante.usuario.get_full_name')

    class Meta:
        model = Pedido
        fields = [
            'id', 'representante', 'representante_nome', 'cliente_nome', 
            'cliente_cnpj', 'status', 'valor_total', 'observacoes', 
            'criado_em', 'itens'
        ]
        read_only_fields = ['representante', 'valor_total', 'status']

    def validate(self, data):
        # 1. Recupera o usuário logado via contexto da requisição
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'perfil_representante'):
            raise serializers.ValidationError("Apenas perfis de Representante podem emitir pedidos.")
            
        representante = request.user.perfil_representante
        limite_desconto = representante.limite_desconto_maximo
        
        # 2. Garante que o pedido não venha vazio
        itens = data.get('itens', [])
        if not itens:
            raise serializers.ValidationError({"itens": "O pedido deve conter pelo menos um item."})
            
        # 3. Validação rígida de desconto linha a linha
        for item in itens:
            desconto = item.get('desconto_percentual', 0)
            if desconto > limite_desconto:
                raise serializers.ValidationError({
                    "desconto_percentual": f"Desconto de {desconto}% bloqueado. Seu limite máximo é {limite_desconto}%."
                })
                
        return data

    @transaction.atomic
    def create(self, validated_data):
        itens_data = validated_data.pop('itens')
        request = self.context.get('request')
        representante = request.user.perfil_representante
        
        # Cria a "capa" do pedido
        pedido = Pedido.objects.create(representante=representante, **validated_data)
        
        valor_total_pedido = 0
        
        # Processa os itens
        for item_data in itens_data:
            produto = item_data['produto']
            quantidade = item_data['quantidade']
            desconto = item_data.get('desconto_percentual', 0)
            
            # REGRA: Fotografia do preço atual no banco
            preco_aplicado = produto.preco_base
            
            # REGRA: Cálculo matemático com Cast para Decimal
            from decimal import Decimal
            valor_bruto = preco_aplicado * quantidade
            valor_desconto = valor_bruto * (Decimal(str(desconto)) / Decimal('100'))
            subtotal = valor_bruto - valor_desconto
            
            # Salva o item
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade=quantidade,
                preco_unitario_aplicado=preco_aplicado,
                desconto_percentual=desconto,
                subtotal=subtotal
            )
            
            valor_total_pedido += subtotal
            
        # Atualiza o total e salva a capa do pedido
        pedido.valor_total = valor_total_pedido
        pedido.save()
        
        return pedido