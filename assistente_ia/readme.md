# 🧠 Módulo: Assistente de Inteligência Artificial (`assistente_ia`)

Este aplicativo é o motor de processamento de linguagem natural do ERP. Ele implementa um pipeline **RAG (Retrieval-Augmented Generation) focado em Text-to-SQL**, permitindo que os usuários consultem o banco de dados do sistema fazendo perguntas comuns, como se estivessem conversando com um analista de dados.

## ✨ Funcionalidades Principais

*   **Tradução Text-to-SQL:** Converte perguntas do usuário ("Qual o produto mais vendido?") em consultas SQL complexas, compreendendo os relacionamentos do schema do banco de dados (tabelas de Vendas, Catálogo e Usuários).
*   **Filtro de Segurança Dinâmico (Multi-Tenant):** O módulo intercepta o Token JWT da requisição, descobre qual é o ID do representante logado e injeta uma regra estrita no *System Prompt* da IA. A IA é obrigada a filtrar os dados de vendas especificamente para aquele usuário.
*   **Auto-Correção e Resiliência (Retry):** Caso a IA gere um SQL com erro de sintaxe, o sistema captura a exceção do banco de dados e envia o erro de volta para a IA, exigindo uma correção automática e invisível para o usuário final (limite de 3 tentativas).
*   **Data-to-Text (Respostas Humanizadas):** Uma vez que os dados brutos são extraídos do banco de dados, uma segunda instância da IA processa esses dicionários e formula uma resposta orgânica e amigável, dispensando o envio de JSONs complexos para o cliente.

## 📂 Estrutura Interna do App

```text
assistente_ia/
├── admin.py
├── apps.py
├── models.py
├── services.py          # O núcleo lógico: Classe AgenteSQL, injeção de schema e comunicação com a LLM
├── tests.py
├── urls.py              # Definição das rotas exclusivas do assistente
└── views.py             # Controladores da API (validação de JWT e acionamento do serviço)
```

## ⚙️ Pré-requisitos e Configuração

Para que este módulo funcione corretamente, ele depende da biblioteca oficial do Google e de uma chave de API válida.

1. **Dependências:** Certifique-se de que `google-generativeai` está instalado no seu ambiente.
2. **Variável de Ambiente:** O aplicativo espera encontrar a variável `GEMINI_API_KEY` carregada no ambiente. Adicione a chave no arquivo `.env` na raiz do projeto principal:

```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio_aqui
```

## 🔄 Como o Pipeline Funciona (Fluxo de Execução)

1. **Requisição HTTP (`views.py`):** O endpoint recebe um `POST` contendo a pergunta do usuário e um cabeçalho `Authorization: Bearer <token>`.
2. **Validação e Contexto:** O Django valida o JWT e extrai a instância do usuário logado.
3. **Serviço Acionado (`services.py`):** A classe `AgenteSQL` é instanciada passando as informações do usuário.
4. **Geração de SQL:** A IA (Gemini 2.5 Flash) gera a consulta baseada no mapeamento do banco de dados.
5. **Execução Segura:** A query roda diretamente no banco de dados da aplicação.
6. **Formulação da Resposta:** Os resultados brutos são repassados à IA, que escreve a resposta final em formato de texto.

## 🌐 Endpoints

### Consultar o Assistente
- **Rota:** `/api/ia/consultar/` (Ajuste o prefixo conforme o roteador global em `setup/urls.py`)
- **Método:** `POST`
- **Autenticação Obrigatória:** Sim (JWT Bearer)

**Exemplo de Payload (Request):**
```json
{
    "pergunta": "Quais são as categorias de produtos que temos no sistema?"
}
```

**Exemplo de Resposta (Response):**
```json
{
    "sucesso": true,
    "tentativas_usadas": 1,
    "query_executada": "SELECT nome FROM catalogo_categoria",
    "resultados_brutos": [
        {"nome": "Proteínas"}, 
        {"nome": "Energéticos"}
    ],
    "resposta_organica": "Atualmente, nós temos as categorias de Proteínas e Energéticos cadastradas no sistema."
}
```

---
*Módulo desenhado para operar com isolamento de contexto e segurança de dados B2B.*
```
