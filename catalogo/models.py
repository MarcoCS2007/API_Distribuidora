from django.db import models
from core.models import BaseModel 

class Categoria(BaseModel):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome

class Produto(BaseModel):
    nome = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT, 
        related_name='produtos'
    )
    preco_base = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.sku} - {self.nome}"