# ia/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import AgenteSQL

class ConsultaIAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pergunta = request.data.get("pergunta")
        
        # 1. Instanciamos a classe passando o usuário logado (A Mágica da Permissão!)
        agente = AgenteSQL(usuario=request.user)
        
        # 2. Chamamos o método principal
        resultado = agente.consultar(pergunta)
        
        if not resultado["sucesso"]:
            return Response(resultado, status=400)
            
        return Response(resultado, status=200)

#DEMO_____________________________________________________________________
from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

def demo_ia(request):
    User = get_user_model()
    
    # 1. Iniciamos um dicionário vazio para mandar para o HTML
    context = {} 

    try:
        # 2. Busca o usuário de demonstração
        usuario_demo = User.objects.get(email='admin@admin.com')
        
        # 3. Gera o token na hora
        token = RefreshToken.for_user(usuario_demo)
        
        # 4. Adiciona o token no dicionário
        context['token_automatico'] = str(token.access_token)
        
    except User.DoesNotExist:
        # 5. Tratamento de erro limpo
        context['token_automatico'] = ''
        context['erro_demo'] = 'Usuário admin@admin.com não encontrado.'
        
    # 6. Manda o request, a tela e o dicionário pronto
    return render(request, 'ia/demo_ia.html', context)