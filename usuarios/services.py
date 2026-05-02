from django.db import transaction
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante

def criar_usuario_com_perfil(validated_data):
    email = validated_data.get('email')
    nome = validated_data.get('nome')
    tipo = validated_data.get('tipo')
    password = validated_data.get('password')

    with transaction.atomic():
        usuario = UsuarioBase.objects.create_user(
            username=email.split('@')[0],  # Django exige username, usamos a parte antes do '@' do email
            email=email,
            tipo=tipo,
            password=password,
            first_name=nome  # Caso queira preencher o nome real no campo first_name
        )

        if tipo == 'GESTOR':
            PerfilGestor.objects.create(
                usuario=usuario,
                departamento='VENDAS',      # Valor padrão genérico
                ramal_interno='0000'        # Valor padrão genérico
            )

        elif tipo == 'REPRESENTANTE':
            PerfilRepresentante.objects.create(
                usuario=usuario,
                telefone_contato='',
                regiao_atuacao='',
                limite_desconto_maximo=0.00,
                meta_mensal=0.00,
                percentual_comissao=1.00
            )
       
        return usuario
        