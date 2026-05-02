from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import BaseModel

# Create your models here.
class UsuarioBase(AbstractUser):
    email = models.EmailField(unique=True)
    
    TIPO_CHOICES = [
        ('GESTOR', 'Gestor'),
        ('REPRESENTANTE', 'Representante'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'tipo']

class PerfilGestor(BaseModel):
    usuario = models.OneToOneField(
        UsuarioBase,
        on_delete=models.CASCADE,
        related_name='perfil_gestor'
    )

    DEPARTAMENTO_CHOICES = [
        ('VENDAS', 'Vendas'),
        ('LOGISTICA', 'Logística'),
    ]
    departamento = models.CharField(
        max_length=20,
        choices=DEPARTAMENTO_CHOICES
    )

    ramal_interno = models.CharField(max_length=20)

class PerfilRepresentante(BaseModel):
    usuario = models.OneToOneField(UsuarioBase, on_delete=models.CASCADE, related_name='perfil_representante')
    telefone_contato = models.CharField(max_length=20)
    regiao_atuacao = models.CharField(max_length=100)
    limite_desconto_maximo = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Ex: 5.00 para 5%")
    meta_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Meta de faturamento no mês")
    percentual_comissao = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Ex: 1.00 para 1% de comissão")

    def __str__(self):
        return f"Rep: {self.usuario.get_full_name()} - {self.regiao_atuacao}"