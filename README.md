# 🏢 ERP B2B API - Sistema de Vendas com Inteligência Artificial

Um sistema de back-end robusto e modular desenvolvido em Django e Django REST Framework (DRF) para gestão de vendas B2B. O sistema gerencia autenticação customizada, catálogo de produtos, processamento de pedidos (com isolamento de dados por representante) e conta com um módulo integrado de Inteligência Artificial para consultas dinâmicas ao banco de dados via linguagem natural (Text-to-SQL RAG).

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Framework:** Django & Django REST Framework (DRF)
- **Banco de Dados:** SQLite (padrão de desenvolvimento)
- **Autenticação:** JSON Web Tokens (JWT) via `rest_framework_simplejwt`
- **Inteligência Artificial:** Google Gemini 2.5 Flash (`google-generativeai`)
- **Segurança & Configuração:** `python-dotenv` para gestão de variáveis de ambiente

## 📦 Arquitetura de Módulos (Apps)

A arquitetura do projeto foi dividida em domínios de negócio isolados, cada um com suas próprias responsabilidades, modelos, serializadores, permissões e rotas:

- **`setup` (Core de Configuração):** Contém as configurações globais do Django (`settings.py`), middlewares e o roteamento principal do projeto.
- **`core`:** Aplicativo destinado a utilitários compartilhados, modelos base e lógicas transversais do sistema.
- **`usuarios`:** Gerencia a identidade e segurança. Substitui o modelo padrão do Django por um sistema baseado em e-mail. Implementa regras de negócio para permissões (Admin vs Representante) e a geração de tokens JWT.
- **`catalogo`:** Módulo de gerenciamento de estoque e portfólio. Controla as entidades de visibilidade global do sistema, como `Categorias` e `Produtos`, incluindo seus preços base e relacionamentos.
- **`vendas`:** O motor transacional do ERP. Gerencia `Pedidos` e `Itens do Pedido`. Possui lógica estrita de *Multi-Tenant*, garantindo que cada pedido esteja vinculado a um representante específico.
- **`assistente_ia`:** O módulo de inovação do sistema. Um pipeline RAG (Retrieval-Augmented Generation) que intercepta perguntas em linguagem natural, traduz para consultas SQL seguras (injetando restrições baseadas no usuário logado), executa no banco e devolve uma resposta processada pela LLM.

## 📂 Estrutura de Diretórios

Abaixo está a estrutura simplificada dos módulos principais do projeto:

```text
.
├── assistente_ia/
│   ├── admin.py, apps.py, models.py
│   ├── services.py          # Lógica do Agente RAG e conexão LLM
│   ├── urls.py, views.py    
├── catalogo/
│   ├── admin.py, apps.py, models.py
│   ├── permissions.py       # Regras de acesso ao catálogo
│   ├── serializers.py, urls.py, views.py
├── core/
│   ├── admin.py, apps.py, models.py, views.py
├── setup/
│   ├── asgi.py, wsgi.py
│   ├── settings.py          # Configurações do Django
│   └── urls.py              # Roteador Global
├── usuarios/
│   ├── admin.py, apps.py, models.py
│   ├── permissions.py       # Níveis de acesso (IsAdmin, IsRepresentante)
│   ├── serializers.py, services.py
│   ├── urls.py, views.py
├── vendas/
│   ├── admin.py, apps.py, models.py
│   ├── permissions.py       # Isolamento de dados (Row-Level Security)
│   ├── serializers.py, urls.py, views.py
├── manage.py
├── requirements.txt
└── README.md
```

## ⚙️ Instalação e Execução Local

Siga os passos abaixo para configurar o ambiente de desenvolvimento local:

### 1. Clone o repositório
```bash
git clone https://github.com/MarcoCS2007/API_Distribuidora.git
cd API_Distribuidora
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

### 4. Configuração de Variáveis de Ambiente (.env)
Crie um arquivo chamado `.env` na raiz do projeto (mesmo diretório do `manage.py`) e insira as chaves de segurança necessárias:
```env
# Chave de segurança do próprio Django
SECRET_KEY=sua_chave_secreta_do_django_aqui

# Chave da API do Google AI Studio para o módulo assistente_ia
GEMINI_API_KEY=sua_chave_gemini_aqui
```
*(Certifique-se de que o `.env` está adicionado ao seu `.gitignore` para não expor suas chaves)*

### 5. Execute as Migrações do Banco de Dados
Gere as tabelas do banco de dados SQLite com os comandos:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Inicie o Servidor
```bash
python manage.py runserver
```
O projeto estará rodando em `http://127.0.0.1:8000/`.

## 🌐 Endpoints e APIs

O sistema utiliza arquitetura RESTful. A aplicação não possui uma lista de endpoints centralizada na raiz, pois o roteamento é modular. Cada App possui seu próprio arquivo `urls.py` e gerencia suas rotas.

As rotas base estão configuradas no diretório `setup/urls.py` e são ramificadas da seguinte forma:
- `/api/usuarios/...` -> Gestão de contas, login e geração de JWT.
- `/api/catalogo/...` -> CRUD de Produtos e Categorias.
- `/api/vendas/...` -> Criação e consulta de Pedidos e Itens (isolados por usuário).
- `/api/ia/...` -> Interação com o assistente inteligente de banco de dados.

*Para consultar os caminhos finais, parâmetros esperados e métodos HTTP, verifique os arquivos `urls.py` e `views.py` de cada respectivo app.*

---
*Desenvolvido com foco em boas práticas de Back-end, Segurança (Multi-Tenant) e Integração de APIs de LLM.*
```
