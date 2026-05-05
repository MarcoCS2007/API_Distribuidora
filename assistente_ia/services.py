# ia/services.py
import os
import google.generativeai as genai
from django.db import connection
from dotenv import load_dotenv

load_dotenv()

class AgenteSQL:
    def __init__(self, usuario):
        """
        Inicia o agente recebendo o usuário logado para aplicar o escopo de dados.
        """
        self.usuario = usuario
        self.limite_tentativas = 3  # Regra 3: Fallback/Retry

        # Configura o cliente do Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # O system_instruction atua como o "cérebro" fixo do agente
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=self._montar_esquema_banco()
        )

    def _montar_esquema_banco(self) -> str:
        schema_base = """
        Você é um assistente de banco de dados SQLite. Sua única função é gerar queries SELECT puras, sem marcação markdown.
        Aqui está o esquema exato do nosso banco de dados:
        
        Tabela: catalogo_categoria (id, nome, descricao)
        Tabela: catalogo_produto (id, nome, sku, preco_base, quantidade_estoque, categoria_id)
        
        Tabela: vendas_pedido (id, cliente_nome, cliente_cnpj, status, valor_total, observacoes, representante_id)
        Tabela: vendas_itempedido (id, quantidade, preco_unitario_aplicado, desconto_percentual, subtotal, pedido_id, produto_id)
        
        Tabela: usuarios_perfilrepresentante (id, limite_desconto_maximo, usuario_id)
        Tabela: usuarios_usuariobase (id, email, nome, tipo)
        
        REGRAS:
        - Para unir pedidos aos representantes, faça JOIN de vendas_pedido com usuarios_perfilrepresentante usando representante_id.
        """
        
        # O resto do código com as permissões dinâmicas continua igual...
        
        # Regra 2: Controle de Permissões (Isolamento de Dados)
        if self.usuario.tipo == 'REPRESENTANTE':
            regra_seguranca = f"""
            ATENÇÃO - REGRA DE SEGURANÇA CRÍTICA:
            O usuário solicitante é um REPRESENTANTE (ID: {self.usuario.id}).
            VOCÊ É OBRIGADO a adicionar 'WHERE representante_id = {self.usuario.id}' 
            em TODAS as consultas que passarem pela tabela vendas_pedido.
            """
            return schema_base + regra_seguranca
            
        elif self.usuario.tipo == 'GESTOR':
            regra_seguranca = "\nO usuário é um GESTOR. Ele tem permissão total de leitura em todas as tabelas."
            return schema_base + regra_seguranca
            
        return schema_base

    def _executar_sql_no_django(self, query: str):
        """Método privado para rodar a string no SQLite"""
        # Trava de segurança no código Python (última linha de defesa)
        if not query.upper().startswith("SELECT"):
            raise ValueError("Query inválida: Apenas comandos SELECT são permitidos.")

        with connection.cursor() as cursor:
            cursor.execute(query)
            colunas = [col[0] for col in cursor.description]
            resultados = cursor.fetchall()
            return [dict(zip(colunas, linha)) for linha in resultados]

    def consultar(self, pergunta: str):
        """Método principal que a View vai chamar (com sistema de Retry)"""
        tentativa_atual = 1
        ultimo_erro = ""

        # Regra 3: Loop de Retry
        while tentativa_atual <= self.limite_tentativas:
            try:
                # 1. Pede para a IA gerar a Query
                prompt = pergunta
                if tentativa_atual > 1:
                    prompt += f"\nNa sua tentativa anterior ocorreu este erro no SQLite: {ultimo_erro}. Por favor, corrija a sintaxe da query."

                resposta_ia = self.model.generate_content(prompt)
                query_gerada = resposta_ia.text.strip().replace("```sql", "").replace("```", "").strip()

                # 2. Tenta executar no banco
                dados = self._executar_sql_no_django(query_gerada)
                
                # ==========================================
                # 3. A NOVA MÁGICA: Transformar dados em texto
                # ==========================================
                prompt_humanizacao = f"""
                O usuário fez a seguinte pergunta: "{pergunta}"
                A busca no sistema retornou os seguintes dados: {dados}
                
                Sua tarefa é responder à pergunta do usuário de forma natural, orgânica e direta, 
                baseando-se APENAS nos dados acima. 
                Não mencione as palavras "JSON", "banco de dados" ou "SQL". Aja como um assistente humano.
                Se os dados estiverem vazios, diga gentilmente que não encontrou informações.
                """
                
                # Criamos uma IA "limpa", sem a regra de gerar apenas SQL
                ia_falante = genai.GenerativeModel("gemini-2.5-flash")
                resposta_final_texto = ia_falante.generate_content(prompt_humanizacao).text.strip()
                # ==========================================

                # Se deu tudo certo, retorna com a resposta humanizada
                return {
                    "sucesso": True,
                    "tentativas_usadas": tentativa_atual,
                    "query_executada": query_gerada,
                    "resultados_brutos": dados,
                    "resposta_organica": resposta_final_texto # <--- A resposta que você queria!
                }

            except Exception as e:
                # Se deu erro, salva o erro para informar a IA na próxima iteração
                ultimo_erro = str(e)
                tentativa_atual += 1

        # Se esgotar as 3 tentativas, desiste graciosamente
        return {
            "sucesso": False,
            "erro": "A inteligência artificial não conseguiu formular uma consulta válida para essa pergunta.",
            "detalhe_tecnico": ultimo_erro
        }