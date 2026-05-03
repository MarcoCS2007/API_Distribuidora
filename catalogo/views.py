from rest_framework import viewsets
from .models import Categoria, Produto
from .serializers import CategoriaSerializer, ProdutoSerializer
from catalogo.permissions import IsGestorVendasOrReadOnly

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.filter(ativo=True)
    serializer_class = CategoriaSerializer
    permission_classes = [IsGestorVendasOrReadOnly]

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.filter(ativo=True)
    serializer_class = ProdutoSerializer
    permission_classes = [IsGestorVendasOrReadOnly]

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save()