from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import  AllowAny, IsAuthenticated
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante
from .serializers import UsuarioBaseSerializer, PerfilGestorSerializer, PerfilRepresentanteSerializer
from .serializers import CadastroUsuarioSerializer
from .services import criar_usuario_com_perfil
from .permissions import PodeCadastrarUsuario, IsLogisticaOrReadOnly

# Create your views here.
class UsuarioBaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLogisticaOrReadOnly]
    queryset = UsuarioBase.objects.filter(ativo=True)
    serializer_class = UsuarioBaseSerializer

    def get_queryset(self):
        qs = UsuarioBase.objects.filter(ativo=True)
        user = self.request.user
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(id=user.id)
        return qs.none()

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.is_active = False
        instance.save()

class PerfilGestorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLogisticaOrReadOnly]
    queryset = PerfilGestor.objects.filter(ativo=True)
    serializer_class = PerfilGestorSerializer

    def get_queryset(self):
        qs = PerfilGestor.objects.filter(ativo=True)
        user = self.request.user
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(usuario=user)
        return qs.none()

    def perform_destroy(self, instance):
        usuario = instance.usuario
        instance.ativo = False
        instance.save()
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()

class PerfilRepresentanteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLogisticaOrReadOnly]
    queryset = PerfilRepresentante.objects.filter(ativo=True)
    serializer_class = PerfilRepresentanteSerializer

    def get_queryset(self):
        qs = PerfilRepresentante.objects.filter(ativo=True)
        user = self.request.user
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(usuario=user)
        return qs.none()

    def perform_destroy(self, instance):
        usuario = instance.usuario
        instance.ativo = False
        instance.save()
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()

class CadastrarUsuarioView(APIView):
    permission_classes = [PodeCadastrarUsuario]

    def post(self, request):
        serializer = CadastroUsuarioSerializer(data=request.data)

        if serializer.is_valid():
            usuario = criar_usuario_com_perfil(serializer.validated_data)
            return Response(
                {"mensagem": "Usuário criado!", "email": usuario.email},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
