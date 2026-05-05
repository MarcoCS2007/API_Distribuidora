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

