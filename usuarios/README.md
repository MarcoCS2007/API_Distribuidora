# App `usuarios` — Documentação Técnica

Documentação do módulo de **autenticação B2B** e **gestão de perfis** (gestores e representantes) integrado ao Django REST Framework (DRF) e **SimpleJWT**.

**Prefixo base das rotas:** conforme `setup/urls.py`, o include aponta para `path('api/usuarios/', include('usuarios.urls'))`. Todas as URLs abaixo assumem o prefixo `/api/usuarios/`.

---

## 1. Visão Geral

O app `usuarios` centraliza:

- **Autenticação:** emissão e renovação de tokens JWT (`login/` e `login/refresh/`), alinhado ao modelo de usuário customizado com login por **e-mail**.
- **Cadastro controlado:** endpoint `POST cadastro/` para criação de novos usuários com perfil associado, sujeito a **autenticação** e a regras de **hierarquia** (`PodeCadastrarUsuario`).
- **Gestão de dados:** ViewSets com CRUD sobre `UsuarioBase`, `PerfilGestor` e `PerfilRepresentante`, restritos a **usuários autenticados**.

O fluxo típico B2B: obter JWT → (conforme papel) cadastrar ou consultar usuários e perfis via API.

---

## 2. Arquitetura

### Service Layer (`services.py`)

A criação de usuário não é feita diretamente na view após a validação do serializer. A função `criar_usuario_com_perfil(validated_data)` concentra a persistência e garante **atomicidade** com `transaction.atomic()`:

- Cria o registro em `UsuarioBase` (senha já tratada por `create_user`).
- Em seguida cria **exatamente um** perfil condicionado ao `tipo`: `PerfilGestor` se `tipo == 'GESTOR'`, ou `PerfilRepresentante` se `tipo == 'REPRESENTANTE'`.

Assim, a view permanece fina (validar → chamar serviço → responder), e falhas no meio do processo não deixam usuário “órfão” sem perfil correspondente, dentro da mesma transação.

---

## 3. Modelagem de Dados

### `UsuarioBase` (`models.py`)

- Herda de `AbstractUser` do Django.
- **`USERNAME_FIELD = 'email'`** — o identificador de login é o e-mail (`email` único).
- **`REQUIRED_FIELDS`** inclui `username` e `tipo` (campos exigidos além do `USERNAME_FIELD` em fluxos como `createsuperuser`).
- Campo **`tipo`**: escolha entre `GESTOR` e `REPRESENTANTE`, definindo qual perfil One-to-One será criado pelo serviço de cadastro.

### Perfis (One-to-One com `UsuarioBase`)

| Modelo | Relacionamento | Campos relevantes |
|--------|----------------|-------------------|
| **`PerfilGestor`** | `usuario` → `OneToOneField(UsuarioBase)`, `related_name='perfil_gestor'` | `departamento` (`VENDAS` \| `LOGISTICA`), `ramal_interno` |
| **`PerfilRepresentante`** | `usuario` → `OneToOneField(UsuarioBase)`, `related_name='perfil_representante'` | `telefone_contato`, `regiao_atuacao`, `limite_desconto_maximo`, `meta_mensal`, `percentual_comissao` |

Ambos os perfis herdam de **`core.models.BaseModel`**: `criado_em`, `atualizado_em`, `ativo`.

---

## 4. Endpoints da API

Todas as rotas abaixo são relativas ao prefixo **`/api/usuarios/`**.

### JWT (SimpleJWT)

| Método | Rota (`urls.py`) | Descrição |
|--------|------------------|-----------|
| `POST` | `login/` | Obtém par de tokens (access + refresh). Corpo usa o campo definido pelo `USERNAME_FIELD` do usuário (`email`) e `password`. |
| `POST` | `login/refresh/` | Renova o access token a partir do `refresh`. |

### Cadastro

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `cadastro/` | Cria usuário + perfil; exige JWT e permissão `PodeCadastrarUsuario`. |

### CRUD — `DefaultRouter`

| Recurso registrado | Listagem / criação | Detalhe (retrieve, update, partial_update, destroy) |
|--------------------|--------------------|------------------------------------------------------|
| `usuarios/` | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` em `usuarios/{id}/` |
| `gestores/` | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` em `gestores/{id}/` |
| `representantes/` | `GET`, `POST` | `GET`, `PUT`, `PATCH`, `DELETE` em `representantes/{id}/` |

**Serializers:** `UsuarioBaseSerializer` expõe `id`, `username`, `email`, `tipo`. `PerfilGestorSerializer` e `PerfilRepresentanteSerializer` usam `fields = '__all__'` (incluem chaves estrangeiras e timestamps herdados de `BaseModel`).

---

## 5. Regras de Negócio e Segurança

### 5.1 Listagens e CRUD de perfis / usuários

- **`UsuarioBaseViewSet`**, **`PerfilGestorViewSet`** e **`PerfilRepresentanteViewSet`** definem `permission_classes = [IsAuthenticated]`.
- Apenas usuários com JWT válido podem acessar listagens e operações CRUD desses ViewSets.

### 5.2 Cadastro (`POST cadastro/`)

- **`IsAuthenticated`:** a rota exige token no header (`Authorization: Bearer <access>`), coerente com o padrão global de autenticação JWT do projeto.
- **`PodeCadastrarUsuario`** (`permissions.py`) aplica a hierarquia:

| Quem | Pode cadastrar |
|------|----------------|
| **Superusuário** (`is_superuser`) | Qualquer perfil (`tipo` no payload sem restrição adicional nesta permissão). |
| **Gestor** com `perfil_gestor.departamento == 'LOGISTICA'` | Apenas novos usuários com **`tipo == 'GESTOR'`** no corpo da requisição. |
| **Gestor** com `perfil_gestor.departamento == 'VENDAS'` | Apenas novos usuários com **`tipo == 'REPRESENTANTE'`**. |
| **Gestor** sem `perfil_gestor` acessível (ex.: `AttributeError`) | **Negado** (falha de integridade / dados inconsistentes tratada como bloqueio). |
| **Representante** (`tipo == 'REPRESENTANTE'`) ou demais casos | **Não** podem cadastrar (`False`). |

O `tipo` avaliado na permissão vem de **`request.data.get('tipo')`** — deve estar presente e coerente com as regras acima.

### 5.3 Serializer de cadastro e integridade via serviço

- **`CadastroUsuarioSerializer`** trata como **obrigatórios:** `email`, `nome`, `tipo`, `password`, `password_confirm`.
- Campos de perfil são **opcionais** (`required=False` e, onde aplicável, `allow_blank=True`): `departamento`, `ramal_interno`, `telefone_contato`, `regiao_atuacao`, `limite_desconto_maximo`, `meta_mensal`, `percentual_comissao`.
- Validações no serializer: confirmação de senha; e-mail único no sistema.

O **`criar_usuario_com_perfil`** aplica **fallbacks** para que o banco receba valores válidos mesmo com payload mínimo:

| Campo / contexto | Comportamento quando omitido ou vazio |
|------------------|----------------------------------------|
| `departamento` | `'VENDAS'` |
| `ramal_interno` | `None` ou string vazia → `'0000'` |
| `telefone_contato` | `None` → `''` |
| `regiao_atuacao` | `None` → `''` |
| `limite_desconto_maximo` | `None` → `0.00` |
| `meta_mensal` | `None` → `0.00` |
| `percentual_comissao` | `None` → `1.00` |

O **`username`** do Django é preenchido automaticamente com a parte local do e-mail (`email.split('@')[0]`). O **`first_name`** recebe o `nome` enviado no cadastro.

---

## 6. Exemplos de payload (JSON)

### 6.1 Login JWT (`POST /api/usuarios/login/`)

O modelo de usuário usa `USERNAME_FIELD = 'email'`; o corpo do SimpleJWT segue esse campo como chave principal de identificação.

**Request:**

```json
{
  "email": "gestor.logistica@empresa.com.br",
  "password": "senha-segura-aqui"
}
```

**Response (exemplo ilustrativo — estrutura típica do SimpleJWT):**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Renovação (`POST /api/usuarios/login/refresh/`):

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 6.2 Cadastro (`POST /api/usuarios/cadastro/`)

Header: `Authorization: Bearer <access_token>`.

**Request — Gestor (campos de perfil parciais; fallbacks no serviço):**

```json
{
  "email": "novo.gestor@empresa.com.br",
  "nome": "Novo Gestor",
  "tipo": "GESTOR",
  "password": "SenhaForte123!",
  "password_confirm": "SenhaForte123!",
  "departamento": "LOGISTICA",
  "ramal_interno": "1234"
}
```

**Request — Representante (muitos campos opcionais):**

```json
{
  "email": "rep.sul@empresa.com.br",
  "nome": "Representante Sul",
  "tipo": "REPRESENTANTE",
  "password": "OutraSenha456!",
  "password_confirm": "OutraSenha456!",
  "telefone_contato": "(11) 99999-0000",
  "regiao_atuacao": "Sul / PR-SC-RS"
}
```

**Response sucesso (`201 Created`):**

```json
{
  "mensagem": "Usuário criado!",
  "email": "novo.gestor@empresa.com.br"
}
```

**Response erro de validação (`400 Bad Request`) — exemplo:**

```json
{
  "email": ["Este e-mail já está cadastrado em nosso sistema."]
}
```

ou

```json
{
  "password": ["As senhas informadas não conferem."]
}
```

Em caso de **403 Forbidden**, o usuário autenticado não satisfaz `PodeCadastrarUsuario` (por exemplo, representante tentando cadastrar ou gestor de vendas tentando criar um `GESTOR`).

---

## 7. Referência rápida de arquivos

| Arquivo | Responsabilidade |
|---------|------------------|
| `models.py` | `UsuarioBase`, `PerfilGestor`, `PerfilRepresentante` |
| `serializers.py` | Serializers de exposição CRUD + `CadastroUsuarioSerializer` |
| `services.py` | `criar_usuario_com_perfil` — transação e defaults |
| `views.py` | ViewSets autenticados + `CadastrarUsuarioView` |
| `permissions.py` | `PodeCadastrarUsuario` — hierarquia de cadastro |
| `urls.py` | Router DRF + JWT + cadastro |

---

*Configuração global relacionada:* `AUTH_USER_MODEL = 'usuarios.UsuarioBase'` e autenticação JWT padrão do DRF em `setup/settings.py`.
