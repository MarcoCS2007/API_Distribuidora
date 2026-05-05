# ⚠️ DEMONSTRAÇÃO: ERP B2B com IA Integrada (Text-to-SQL RAG)

> 🚨 **AVISO IMPORTANTE:** Esta branch (`demo-AI`) foi criada EXCLUSIVAMENTE para fins de portfólio, apresentação e testes locais. Ela contém atalhos de desenvolvimento (como a geração e injeção automática de tokens JWT de administrador no Front-end) para melhorar a Developer Experience (DX) durante demonstrações. **Este código não deve ser levado para um ambiente de produção.** Para a versão oficial e segura do back-end, acesse a branch `main`.

Um sistema de back-end robusto para gestão de vendas B2B, potencializado por um Assistente Virtual de Inteligência Artificial. Esta versão inclui uma interface visual acoplada para facilitar a interação com a IA utilizando linguagem natural.

## 🎯 Sobre a Demonstração

O objetivo desta branch é provar o funcionamento do nosso pipeline **RAG (Retrieval-Augmented Generation)** em 2 passos diretamente no navegador, sem a necessidade de ferramentas externas como Postman ou Insomnia.

### O que tem de diferente nesta branch?
- **Interface Gráfica (UI):** Uma tela HTML/JS Vanilla renderizada pelo próprio Django para interação em formato de chat.
- **Injeção de Token (Plug & Play):** Ao acessar a tela de demonstração, o backend gera automaticamente um Token JWT de acesso (simulando o usuário Admin) para que recrutadores ou avaliadores possam testar a IA instantaneamente, com zero atrito.
- **Isolamento de Dados Mantido:** Mesmo na demo, a Inteligência Artificial obedece à regra de *Row-Level Security*, injetando o ID do usuário nos prompts SQL para evitar vazamento de dados.

## 🛠️ Tecnologias e Stack

- **Back-end:** Python 3, Django & Django REST Framework (DRF)
- **Inteligência Artificial:** Google Gemini 2.5 Flash (`google-generativeai`)
- **Autenticação:** JSON Web Tokens (JWT)
- **Front-end (Demo):** HTML5, CSS3, Vanilla JavaScript
- **Banco de Dados:** SQLite

## 📂 Arquitetura do App de Inteligência Artificial (`ia`)

Nesta branch, o aplicativo `ia` ganha protagonismo com a inclusão de templates visuais:

```text
ia/
├── services.py          # Lógica do Agente RAG (Text-to-SQL e humanização da resposta)
├── views.py             # Endpoints da API e View especial que gera o Token Automático
├── urls.py              # Rotas da API e da interface
└── templates/
    └── ia/demo_ia.html  # 🌟 Interface Front-end da Demonstração
```

## 🚀 Como Executar a Demo Localmente

### 1. Clone o repositório e mude para a branch da Demo
```bash
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio
git checkout demo-AI
```

### 2. Prepare o Ambiente Virtual e Dependências
```bash
python -m venv venv
# Ative o venv (Windows: venv\Scripts\activate | Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto e adicione sua chave de API do Google AI Studio:
```env
GEMINI_API_KEY=sua_chave_secreta_aqui
```

### 4. Execute as Migrações
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. ⚠️ PASSO CRÍTICO: Crie o Usuário da Demo
Para que a injeção automática de token funcione na tela de teste, o sistema procura por um usuário específico. Você **precisa** criar um superusuário com este e-mail:
```bash
python manage.py createsuperuser
# Quando pedir o e-mail, digite: admin@admin.com
# A senha pode ser qualquer uma de sua escolha.
```
*Dica: Acesse `http://127.0.0.1:8000/admin/` para popular o banco com categorias, produtos e pedidos para a IA ter o que buscar!*

### 6. Inicie o Servidor e Teste a Magia
```bash
python manage.py runserver
```
Abra o seu navegador e acesse a interface da IA:
👉 **[http://127.0.0.1:8000/api/assistente-ia/demo/](http://127.0.0.1:8000/api/assistente-ia/demo/)**

## 💡 O que perguntar para a IA?
Teste o processamento de linguagem natural com perguntas como:
- *"Quais são as categorias de produtos que temos no sistema?"* 
- *"Temos algum produto da categoria Proteínas?"*
- *"Qual foi o maior pedido registrado e qual o representante fez a venda?"* 

---
*Branch destinada à demonstração de habilidades em Engenharia de Software, Integração de LLMs e Experiência do Desenvolvedor (DX).*
```
