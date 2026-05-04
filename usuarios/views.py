from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from .models import UsuarioBase, PerfilGestor, PerfilRepresentante
from .serializers import UsuarioBaseSerializer, PerfilGestorSerializer, PerfilRepresentanteSerializer, CadastroUsuarioSerializer
from .services import criar_usuario_com_perfil
from .permissions import PodeCadastrarUsuario, IsLogisticaOrReadOnly

# ViewSet responsável pelas operações de CRUD (Listar, Criar, Atualizar, Deletar) do modelo base de Usuário
class UsuarioBaseViewSet(viewsets.ModelViewSet):
    # Define que apenas a Logística pode editar/deletar. Outros apenas lêem (se passarem no filtro)
    permission_classes = [IsLogisticaOrReadOnly]
    # Busca inicial padrão filtrando apenas usuários ativos
    queryset = UsuarioBase.objects.filter(ativo=True)
    # Define o serializador que transforma os dados complexos do banco em JSON e vice-versa
    serializer_class = UsuarioBaseSerializer

    # Sobrescreve a busca de dados para garantir o isolamento de privacidade (IDOR)
    def get_queryset(self):
        # Previne Erro 500 caso um usuário não logado tente acessar a rota (retorna lista vazia)
        if not self.request.user.is_authenticated:
            return self.queryset.none()
            
        # qs (queryset) armazena a lista base de usuários que não foram deletados
        qs = UsuarioBase.objects.filter(ativo=True)
        # user armazena a instância do usuário que está fazendo a requisição neste exato momento
        user = self.request.user
        
        # Se for administrador de sistema ou Gestor, devolve a lista completa
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        # Se for Representante, filtra a lista (qs) para retornar APENAS o registro dele mesmo
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(id=user.id)
        
        # Retorno de segurança: se não cair em nenhuma regra acima, retorna nada
        return qs.none()

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    # Sobrescreve a exclusão padrão do banco de dados para realizar o "Soft-Delete"
    def perform_destroy(self, instance):
        # instance representa o usuário específico sendo "deletado" na requisição
        instance.ativo = False # Oculta o usuário do sistema
        instance.is_active = False # Bloqueia o token/login no fluxo nativo do Django
        instance.save() # Salva o novo estado no banco

# ViewSet responsável pelo CRUD exclusivo dos detalhes do Perfil Gestor
class PerfilGestorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLogisticaOrReadOnly]
    queryset = PerfilGestor.objects.filter(ativo=True)
    serializer_class = PerfilGestorSerializer

    # Filtra a visualização dos perfis com base em quem está acessando
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
            
        qs = PerfilGestor.objects.filter(ativo=True)
        user = self.request.user
        
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(usuario=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    # Soft-Delete em cascata (Desativa o Perfil + a Conta de Login vinculada)
    def perform_destroy(self, instance):
        # usuario extrai a conta base vinculada a este perfil específico
        usuario = instance.usuario
        
        # Desativa primeiro o perfil
        instance.ativo = False
        instance.save()
        
        # Depois, desativa a conta de acesso associada a ele
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()

# ViewSet responsável pelo CRUD exclusivo dos detalhes do Perfil Representante
class PerfilRepresentanteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLogisticaOrReadOnly]
    queryset = PerfilRepresentante.objects.filter(ativo=True)
    serializer_class = PerfilRepresentanteSerializer

    # Garante que um representante jamais veja os dados de vendas/região de outro representante
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
            
        qs = PerfilRepresentante.objects.filter(ativo=True)
        user = self.request.user
        
        if user.is_superuser or getattr(user, 'tipo', None) == 'GESTOR':
            return qs
        if getattr(user, 'tipo', None) == 'REPRESENTANTE':
            return qs.filter(usuario=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    # Soft-Delete em cascata idêntico ao do Gestor
    def perform_destroy(self, instance):
        usuario = instance.usuario
        instance.ativo = False
        instance.save()
        usuario.ativo = False
        usuario.is_active = False
        usuario.save()

# View isolada responsável pelo processo de Cadastro Unificado (Conta + Perfil)
class CadastrarUsuarioView(APIView):
    # Apenas cargos específicos podem cadastrar outros baseados na hierarquia (ex: Logística cria Gestor)
    permission_classes = [PodeCadastrarUsuario]

    # Processa as requisições POST (criação de recursos)
    def post(self, request):
        # Passa o JSON recebido (request.data) para o serializador limpar e checar tipagem/regras
        serializer = CadastroUsuarioSerializer(data=request.data)

        # Se os dados passarem nas validações (ex: senha forte, e-mail único, formato correto)
        if serializer.is_valid():
            # Envia os dados limpos (validated_data) para a camada de serviço criar os registros de forma atômica
            usuario = criar_usuario_com_perfil(serializer.validated_data)
            
            # Retorna uma resposta HTTP 201 (Sucesso na criação) com uma confirmação amigável
            return Response(
                {"mensagem": "Usuário criado!", "email": usuario.email},
                status=status.HTTP_201_CREATED
            )
        else:
            # Se falhar, devolve um dicionário com os campos exatos que deram erro (HTTP 400 - Erro do cliente)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
