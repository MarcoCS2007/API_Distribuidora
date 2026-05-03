from django.db import transaction
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante

def criar_usuario_com_perfil(validated_data):
    email = validated_data.get('email')
    nome = validated_data.get('nome')
    tipo = validated_data.get('tipo')
    password = validated_data.get('password')

    departamento = validated_data.get('departamento') or 'VENDAS'
    ramal = validated_data.get('ramal_interno')
    if ramal is None or ramal == '':
        ramal = '0000'

    telefone = validated_data.get('telefone_contato')
    if telefone is None:
        telefone = ''
    regiao = validated_data.get('regiao_atuacao')
    if regiao is None:
        regiao = ''

    limite = validated_data.get('limite_desconto_maximo')
    if limite is None:
        limite = 0.00
    meta = validated_data.get('meta_mensal')
    if meta is None:
        meta = 0.00
    comissao = validated_data.get('percentual_comissao')
    if comissao is None:
        comissao = 1.00

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
                departamento=departamento,
                ramal_interno=ramal,
            )

        elif tipo == 'REPRESENTANTE':
            PerfilRepresentante.objects.create(
                usuario=usuario,
                telefone_contato=telefone,
                regiao_atuacao=regiao,
                limite_desconto_maximo=limite,
                meta_mensal=meta,
                percentual_comissao=comissao,
            )
       
        return usuario
        