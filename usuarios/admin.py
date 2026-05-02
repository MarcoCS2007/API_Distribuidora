# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante

@admin.register(UsuarioBase)
class UsuarioBaseAdmin(UserAdmin):
    # Adiciona o nosso campo 'tipo' na tela de listagem do admin
    list_display = ('email', 'username', 'tipo', 'is_staff', 'is_active')
    
    # Adiciona o campo 'tipo' na tela de edição do usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Corporativas', {'fields': ('tipo',)}),
    )

@admin.register(PerfilGestor)
class PerfilGestorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'departamento', 'ramal_interno', 'ativo')
    list_filter = ('departamento', 'ativo')
    search_fields = ('usuario__email', 'usuario__first_name')

@admin.register(PerfilRepresentante)
class PerfilRepresentanteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'regiao_atuacao', 'percentual_comissao', 'meta_mensal', 'ativo')
    list_filter = ('regiao_atuacao', 'ativo')
    search_fields = ('usuario__email', 'usuario__first_name')