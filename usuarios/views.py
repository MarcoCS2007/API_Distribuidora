from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import  AllowAny, IsAuthenticated
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante
from .serializers import UsuarioBaseSerializer, PerfilGestorSerializer, PerfilRepresentanteSerializer
from .serializers import CadastroUsuarioSerializer
from .services import criar_usuario_com_perfil
from .permissions import PodeCadastrarUsuario

# Create your views here.
class UsuarioBaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UsuarioBase.objects.all()
    serializer_class = UsuarioBaseSerializer

class PerfilGestorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PerfilGestor.objects.all()
    serializer_class = PerfilGestorSerializer

class PerfilRepresentanteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = PerfilRepresentante.objects.all()
    serializer_class = PerfilRepresentanteSerializer

class CadastrarUsuarioView(APIView):
    permission_classes = [IsAuthenticated, PodeCadastrarUsuario]

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
       
