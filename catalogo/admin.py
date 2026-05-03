from django.contrib import admin
from .models import Categoria, Produto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'ativo')
    search_fields = ('nome',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'nome',
        'categoria',
        'preco_base',
        'quantidade_estoque',
        'ativo',
    )
    list_filter = ('categoria', 'ativo')
    search_fields = ('sku', 'nome')
