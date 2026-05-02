from rest_framework import serializers
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante

class UsuarioBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioBase
        fields = ['id', 'username', 'email', 'tipo']

class PerfilGestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilGestor
        fields = '__all__'

class PerfilRepresentanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilRepresentante
        fields = '__all__'

class CadastroUsuarioSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nome = serializers.CharField(max_length=150)
    tipo = serializers.ChoiceField(choices=UsuarioBase.TIPO_CHOICES)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

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

