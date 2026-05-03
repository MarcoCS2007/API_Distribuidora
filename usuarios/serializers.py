from rest_framework import serializers
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante

class UsuarioBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioBase
        fields = ['id', 'username', 'email', 'tipo', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'tipo': {'read_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        usuario = UsuarioBase.objects.create(**validated_data)
        if password:
            usuario.set_password(password)
            usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class PerfilGestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilGestor
        fields = '__all__'
        extra_kwargs = {
            'usuario': {'read_only': True},
        }

class PerfilRepresentanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilRepresentante
        fields = '__all__'
        extra_kwargs = {
            'usuario': {'read_only': True},
        }

class CadastroUsuarioSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nome = serializers.CharField(max_length=150)
    tipo = serializers.ChoiceField(choices=UsuarioBase.TIPO_CHOICES)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    departamento = serializers.ChoiceField(
        choices=PerfilGestor.DEPARTAMENTO_CHOICES,
        required=False,
    )
    ramal_interno = serializers.CharField(max_length=20, required=False, allow_blank=True)

    telefone_contato = serializers.CharField(max_length=20, required=False, allow_blank=True)
    regiao_atuacao = serializers.CharField(max_length=100, required=False, allow_blank=True)
    limite_desconto_maximo = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )
    meta_mensal = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    percentual_comissao = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )

    def validate(self, data):
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        email = data.get('email')

        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({
                'password': 'As senhas informadas não conferem.'
            })

        if UsuarioBase.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "Este e-mail já está cadastrado em nosso sistema."
            })

        return data

