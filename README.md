# 🤖 ERP B2B com IA Integrada (Text-to-SQL RAG)

Um sistema de back-end robusto para gestão de vendas B2B, potencializado por um Assistente Virtual de Inteligência Artificial. O sistema permite que representantes comerciais consultem dados de catálogo, estoque e histórico de vendas utilizando linguagem natural, com isolamento rigoroso de dados (Multi-Tenant) e segurança baseada em JWT.

## 🎯 Sobre o Projeto

O diferencial deste projeto é a integração profunda de um pipeline **RAG (Retrieval-Augmented Generation)** em 2 passos diretamente com o banco de dados da aplicação, garantindo que a IA gere relatórios dinâmicos sem comprometer a segurança da informação.

### Principais Funcionalidades
- **Text-to-SQL + Data-to-Text:** A IA (Gemini 2.5 Flash) traduz a pergunta do usuário para uma query SQL otimizada, o backend executa no banco e devolve os dados para a IA formular uma resposta humana e orgânica.
- **Isolamento de Dados (Row-Level Security Dinâmico):** A inteligência artificial é instruída através do *System Prompt* a filtrar automaticamente as consultas de vendas pelo `ID` do representante logado via token JWT. Um representante jamais tem acesso aos dados de outro.
- **Resiliência (Auto-Retry):** Sistema de tratamento de exceções onde o backend captura eventuais erros de sintaxe SQL gerados pela IA e exige uma auto-correção iterativa (com limite de tentativas) antes de falhar a requisição.
- **Ambiente de Demonstração (DX):** Interface gráfica acoplada na branch `demo-AI` para testes rápidos sem necessidade de ferramentas externas como Postman.

## 🛠️ Tecnologias e Stack

- **Linguagem:** Python 3
- **Framework Back-end:** Django & Django REST Framework (DRF)
- **Banco de Dados:** SQLite (Desenvolvimento)
- **Inteligência Artificial:** Google Gemini 2.5 Flash (`google-generativeai`)
- **Autenticação:** JSON Web Tokens (JWT) via `rest_framework_simplejwt`
- **Variáveis de Ambiente:** `python-dotenv`

## 📦 Arquitetura de Módulos (Apps)

O projeto é dividido em domínios de negócio claros:

*   **`usuarios`**: Gestão de identidade. Abandona o modelo padrão do Django em favor de login via E-mail e gerencia os papéis (Admin vs Representante).
*   **`catalogo`**: Gestão global de `Categorias` e `Produtos` (Suplementação esportiva).
*   **`vendas`**: Motor transacional. Relaciona `Pedidos` e `Itens do Pedido` com vínculo obrigatório ao ID do representante logado.
*   **`ia`**: O cérebro do assistente virtual. Contém os *Services* (AgenteSQL) responsáveis pela comunicação com a API do Google e injeção do schema do banco.

## 📂 Estrutura de Diretórios (Tree)

```text
meu_projeto_erp/
├── manage.py
├── meu_projeto_erp/         # Configurações globais (settings.py, urls.py)
├── usuarios/                # App de Autenticação Customizada
├── catalogo/                # App de Produtos e Categorias
├── vendas/                  # App de Pedidos (Multi-tenant)
├── ia/                      # App de Inteligência Artificial
│   ├── services.py          # Lógica do Agente RAG (Text-to-SQL)
│   ├── views.py             # Endpoints da API e Views de Demonstração
│   ├── urls.py              # Rotas da IA
│   └── templates/
│       └── ia/demo_ia.html  # Interface Front-end Vanilla JS
├── testar_ia.py             # Script utilitário de diagnóstico da API Google
├── .env                     # Variáveis de ambiente (ignorado no git)
└── requirements.txt         # Dependências do projeto
```

## 🚀 Como Executar o Projeto Localmente

### 1. Clone o repositório
```bash
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto (mesmo nível do `manage.py`) e adicione sua chave de API do Google AI Studio:
```env
GEMINI_API_KEY=sua_chave_secreta_aqui
```

### 5. Execute as Migrações do Banco de Dados
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie o usuário de demonstração e popule o banco
```bash
python manage.py createsuperuser
# Dica: Crie o usuário admin@admin.com para testar a interface de demonstração visual
```
*Acesse `http://127.0.0.1:8000/admin/` para cadastrar algumas categorias, produtos e pedidos fictícios.*

### 7. Inicie o Servidor
```bash
python manage.py runserver
```

## 🌐 Endpoints Principais

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/usuarios/login/` | Autentica o usuário e retorna `access` e `refresh` tokens. | Nenhuma |
| `POST` | `/api/assistente-ia/consultar/` | Recebe a pergunta em linguagem natural e retorna a resposta da IA baseada nos dados. | JWT Bearer |
| `GET` | `/api/ia/demo/` | Acesso à tela de demonstração HTML/JS (Gera token automático para `admin@admin.com`). | Opcional |

## 💡 Exemplos de Perguntas para a IA
- *"Quais são as categorias de produtos cadastradas no sistema?"* (Busca global)
- *"Qual produto eu mais vendi este mês?"* (Busca restrita ao Representante)
- *"Quantos pedidos estão registrados no meu nome?"* (Busca restrita ao Representante)

---
*Desenvolvido com foco em boas práticas de Back-end, Segurança e Integração LLM.*
```
