# Módulo `usuarios` — Referência técnica

Documentação de referência para **desenvolvedores backend**, **integração de APIs** e **frontends** que consomem o domínio de identidade, autenticação e perfis hierárquicos da distribuidora.

**Contratos globais**

| Item | Valor |
|------|--------|
| **Prefixo HTTP** | `/api/usuarios/` (definido em `setup/urls.py` → `usuarios.urls`) |
| **Framework** | Django REST Framework (DRF) + **Simple JWT** para tokens |
| **Modelo de usuário** | `AUTH_USER_MODEL = 'usuarios.UsuarioBase'` |
| **Formato de corpo** | `application/json` (salvo indicação contrária) |

---

## 1. Visão geral e arquitetura

### 1.1 Papel do módulo

O app `usuarios` concentra:

- **Autenticação stateless** via JWT (emissão e renovação de tokens).
- **Cadastro transacional** de conta + **exatamente um** perfil (`PerfilGestor` **ou** `PerfilRepresentante`), apenas via **`POST /cadastro/`**, com política MVP: **superusuário** cria **gestores** (e pode criar representantes); **gestor de Vendas** cria **somente representantes**; **Logística não cadastra** usuários por esta rota.
- **CRUD restrito** sobre `UsuarioBase`, `PerfilGestor` e `PerfilRepresentante`, com **filtros anti-IDOR** e **soft-delete** onde aplicável.

### 1.2 Camadas e fluxo de dados

```
Cliente (JSON)
    → View / ViewSet (DRF)
        → Serializer (validação de entrada)
        → [Cadastro] services.criar_usuario_com_perfil + transaction.atomic()
        → Modelos Django → PostgreSQL/SQLite (conforme settings)
```

| Camada | Arquivo(s) | Responsabilidade |
|--------|------------|------------------|
| **Rotas** | `usuarios/urls.py` | `DefaultRouter` (recursos REST) + rotas JWT + `cadastro/` |
| **Views** | `usuarios/views.py` | ViewSets + `CadastrarUsuarioView` (`APIView`) |
| **Serviço** | `usuarios/services.py` | `criar_usuario_com_perfil`: persistência atômica usuário + perfil |
| **Serialização** | `usuarios/serializers.py` | Validação, exposição de campos, regras de escrita |
| **Autorização** | `usuarios/permissions.py` | `PodeCadastrarUsuario`, `IsLogisticaOrReadOnly` |
| **Modelagem** | `usuarios/models.py` | `UsuarioBase`, `PerfilGestor`, `PerfilRepresentante` |

### 1.3 Modelos (resumo de schema)

**`UsuarioBase`** (`AbstractUser`)

- Identificador de login: **`email`** (`USERNAME_FIELD`); campo `username` ainda existe (preenchido pelo serviço de cadastro a partir da parte local do e-mail).
- **`tipo`**: `GESTOR` | `REPRESENTANTE`.
- **`ativo`**: flag de negócio (listagens e regras de visibilidade); complementar a `is_active` do Django Auth.

**`PerfilGestor`** (`core.models.BaseModel` + `OneToOne` → `UsuarioBase`)

- `departamento`: `VENDAS` | `LOGISTICA`
- `ramal_interno`: `CharField(max_length=20)`
- Metadados herdados: `criado_em`, `atualizado_em`, `ativo`

**`PerfilRepresentante`** (`BaseModel` + `OneToOne` → `UsuarioBase`)

- `telefone_contato`, `regiao_atuacao`, `limite_desconto_maximo`, `meta_mensal`, `percentual_comissao` (defaults no modelo; o serviço aplica fallbacks quando o payload omite valores).

---

## 2. Regras de negócio

### 2.1 Hierarquia de cadastro (`POST /api/usuarios/cadastro/`)

A permissão **`PodeCadastrarUsuario`** (`permissions.py`) implementa a política atual do MVP. O **`tipo`** solicitado vem do corpo JSON (`request.data.get('tipo')`).

| Autenticado como | Pode usar `POST /cadastro/` |
|------------------|------------------------------|
| **`is_superuser`** (Administrador do Sistema) | **Único** autorizado a criar contas **`tipo: "GESTOR"`**. Pode também criar **`tipo: "REPRESENTANTE"`**. |
| **Gestor** com `perfil_gestor.departamento == 'VENDAS'` | **Somente** **`tipo: "REPRESENTANTE"`**. Tentativa com **`tipo: "GESTOR"`** → **`403 Forbidden`**. |
| **Gestor** com `perfil_gestor.departamento == 'LOGISTICA'` | **Nenhuma** criação permitida → **`403 Forbidden`**. |
| **Representante** ou gestor sem `perfil_gestor` | **Negado** (`403 Forbidden`) |

**Resumo operacional**

- **`GESTOR`:** criação **exclusiva do superusuário** (não há delegação a gestores de Logística ou Vendas).
- **`REPRESENTANTE`:** gestores de **Vendas** **ou** **superusuário**.
- **Logística:** **não** cadastra usuários pela API.

**Efeito no banco** (`services.criar_usuario_com_perfil`):

- `tipo == 'GESTOR'` → cria `UsuarioBase` + **`PerfilGestor`** (`departamento` default `VENDAS` se omitido; `ramal_interno` default `'0000'` se vazio).
- `tipo == 'REPRESENTANTE'` → cria `UsuarioBase` + **`PerfilRepresentante`** (strings vazias e decimais default conforme serviço).

Toda a operação ocorre dentro de **`transaction.atomic()`** — falha no meio não deixa usuário sem perfil correspondente.

### 2.2 Bloqueio arquitetural: criação apenas via `/cadastro/`

- **Única rota suportada** para **criar** novos usuários/perfis no MVP: **`POST /api/usuarios/cadastro/`**.
- Os ViewSets `UsuarioBaseViewSet`, `PerfilGestorViewSet` e `PerfilRepresentanteViewSet` **sobrescrevem `create`** e respondem **`405 Method Not Allowed`** para **`POST`** nas coleções (`/usuarios/`, `/gestores/`, `/representantes/`).
- Motivação: o serializer de usuário base (`UsuarioBaseSerializer`) não cria perfil vinculado; apenas `cadastro/` + serviço garantem **usuário + perfil** coerentes.

### 2.3 Visibilidade de dados (queryset)

- **Listagens e retrieve** usam querysets filtrados por **`ativo=True`** nos três recursos.
- **Representantes** enxergam **apenas** o próprio usuário / perfil (ver §3.1 — IDOR).
- **Gestores** e **superusuários** enxergam o conjunto completo (ainda restrito a `ativo=True` na camada de queryset base).

### 2.4 Exclusão lógica (soft-delete)

Não há remoção física (`DELETE` SQL) nas rotas documentadas. Todas as exclusões são **lógicas**: campos **`ativo=False`** (modelos de negócio / `BaseModel`) e **`is_active=False`** (`UsuarioBase` / Django Auth), de forma que o login e tokens deixem de ser válidos para a política de autenticação configurada.

**Cascata:** ao desativar um **perfil** (`PerfilGestor` ou `PerfilRepresentante`), o **`UsuarioBase`** vinculado é sempre desativado na mesma operação. Ao desativar pelo endpoint de **`UsuarioBase`**, o código desativa também o **perfil** associado (gestor ou representante), quando existir, antes de desativar a conta — mantendo **conta + perfil** alinhados.

| Recurso alvo | Método | Efeito em `perform_destroy` |
|--------------|--------|-------------------------------|
| **`/usuarios/{id}/`** | `DELETE` | Se existir **`perfil_gestor`** ou **`perfil_representante`**, define **`ativo=False`** no perfil; em seguida **`UsuarioBase`**: `ativo=False`, `is_active=False`. |
| **`/gestores/{id}/`** | `DELETE` | **`PerfilGestor`**: `ativo=False`; depois **`UsuarioBase`** vinculado: `ativo=False`, `is_active=False`. |
| **`/representantes/{id}/`** | `DELETE` | **`PerfilRepresentante`**: `ativo=False`; depois **`UsuarioBase`** vinculado: `ativo=False`, `is_active=False`. |

**Resposta HTTP:** em sucesso, o DRF costuma retornar **`204 No Content`** para `destroy`.

---

## 3. Segurança e permissões

### 3.1 Proteção contra IDOR (`get_queryset`)

Em **`UsuarioBaseViewSet`**, **`PerfilGestorViewSet`** e **`PerfilRepresentanteViewSet`**:

- Requisições **não autenticadas** recebem queryset vazio (evita vazamento antes da camada de permissão em alguns fluxos).
- **`tipo == 'REPRESENTANTE'`**:
  - `usuarios/` → somente `id == request.user.id`
  - `gestores/` e `representantes/` → somente registros com `usuario=request.user`
- **`tipo == 'GESTOR'`** ou **`is_superuser`**: acesso ao queryset completo (filtrado por `ativo=True`).
- Demais casos: queryset vazio.

Assim, um representante **não** consegue enumerar ou abrir detalhe de outros usuários/perfis por troca de `id` na URL (salvo bug de permissão em outra camada).

### 3.2 Permissões DRF

**`IsLogisticaOrReadOnly`** (ViewSets de `usuarios`, `gestores`, `representantes`)

| Método | Quem passa |
|--------|------------|
| `GET`, `HEAD`, `OPTIONS` | Qualquer usuário **autenticado** |
| `POST` | **Não aplicável** aos ViewSets de coleção — retorno **`405`** (ver §2.2) |
| `PUT`, `PATCH`, `DELETE` | **`is_superuser`** **ou** gestor com **`perfil_gestor.departamento == 'LOGISTICA'`** |

**`PodeCadastrarUsuario`** (`CadastrarUsuarioView` — somente `POST /cadastro/`)

- Requer **JWT** válido.
- **`is_superuser`:** permitido (criação de `GESTOR` e/ou `REPRESENTANTE` conforme o `tipo` no JSON).
- **Gestor de Vendas:** somente se `tipo == 'REPRESENTANTE'`.
- **Gestor de Logística, representantes e demais:** **negado** (`403`).

Não confundir com **`IsLogisticaOrReadOnly`**: a Logística continua podendo **alterar / excluir** registros nos ViewSets (ver tabela abaixo), mas **não** cria contas via `cadastro/`.

### 3.3 Campos sensíveis e imutáveis nos serializers

**`UsuarioBaseSerializer`**

| Campo | Comportamento |
|-------|----------------|
| `password` | **Write-only** — nunca serializado em respostas de leitura; em `update`, se enviado, dispara `set_password`. |
| `tipo` | **Read-only** — não pode ser alterado via este serializer (alinhado ao fluxo de cadastro controlado). |

**`PerfilGestorSerializer` / `PerfilRepresentanteSerializer`**

- `usuario`: **read-only** — vínculo não deve ser trocado pela API de perfil.

**`CadastroUsuarioSerializer`**

- `password` e `password_confirm`: campos de entrada; **não** entram no payload de sucesso `201` (apenas `mensagem` + `email`).

### 3.4 Cabeçalho de autenticação (JWT)

Para rotas protegidas (cadastro, ViewSets, refresh com política padrão):

```http
Authorization: Bearer <access_token>
```

---

## 4. Endpoints (rotas)

Todas as URLs abaixo são relativas ao host da API (ex.: `https://api.exemplo.com`).

### 4.1 JWT (SimpleJWT)

| Método | Caminho completo | View | Descrição |
|--------|------------------|------|-----------|
| `POST` | `/api/usuarios/login/` | `TokenObtainPairView` | Obtém `access` + `refresh`. Corpo: credenciais alinhadas ao `USERNAME_FIELD` (**`email`**) e **`password`**. |
| `POST` | `/api/usuarios/login/refresh/` | `TokenRefreshView` | Novo `access` a partir de **`refresh`**. |

### 4.2 Cadastro transacional

| Método | Caminho completo | View | Permissão |
|--------|------------------|------|-----------|
| `POST` | `/api/usuarios/cadastro/` | `CadastrarUsuarioView` | `PodeCadastrarUsuario` |

### 4.3 Router (`DefaultRouter`)

Substitua `{id}` pelo PK inteiro do registro.

#### `UsuarioBase`

| Método | Caminho | Ação |
|--------|---------|------|
| `GET` | `/api/usuarios/usuarios/` | Lista (filtrada por papel — §3.1) |
| `POST` | `/api/usuarios/usuarios/` | **`405`** — usar `cadastro/` |
| `GET` | `/api/usuarios/usuarios/{id}/` | Detalhe |
| `PUT` | `/api/usuarios/usuarios/{id}/` | Substituição completa (permissão logística — §3.2) |
| `PATCH` | `/api/usuarios/usuarios/{id}/` | Atualização parcial |
| `DELETE` | `/api/usuarios/usuarios/{id}/` | Soft-delete do usuário (§2.4) |

#### `PerfilGestor`

| Método | Caminho | Ação |
|--------|---------|------|
| `GET` | `/api/usuarios/gestores/` | Lista |
| `POST` | `/api/usuarios/gestores/` | **`405`** |
| `GET` | `/api/usuarios/gestores/{id}/` | Detalhe |
| `PUT` / `PATCH` | `/api/usuarios/gestores/{id}/` | Atualização |
| `DELETE` | `/api/usuarios/gestores/{id}/` | Soft-delete perfil + usuário (§2.4) |

#### `PerfilRepresentante`

| Método | Caminho | Ação |
|--------|---------|------|
| `GET` | `/api/usuarios/representantes/` | Lista |
| `POST` | `/api/usuarios/representantes/` | **`405`** |
| `GET` | `/api/usuarios/representantes/{id}/` | Detalhe |
| `PUT` / `PATCH` | `/api/usuarios/representantes/{id}/` | Atualização |
| `DELETE` | `/api/usuarios/representantes/{id}/` | Soft-delete perfil + usuário (§2.4) |

### 4.4 Códigos HTTP frequentes

| Código | Contexto típico |
|--------|-------------------|
| `200` / `204` | Leitura / exclusão bem-sucedida |
| `201` | Cadastro em `/cadastro/` |
| `400` | Validação do serializer (ex.: e-mail duplicado, senhas diferentes) |
| `401` | Token ausente ou inválido |
| `403` | Autenticado mas sem permissão (ex.: representante em `cadastro/`, gestor de Logística em `cadastro/`, gestor de Vendas com `tipo: "GESTOR"`) |
| `405` | `POST` em coleções dos ViewSets acima |

---

## 5. Exemplos de uso (JSON)

### 5.1 Login — `POST /api/usuarios/login/`

**Request**

```json
{
  "email": "gestor.vendas@empresa.com.br",
  "password": "SenhaSegura123!"
}
```

**Response `200 OK`** (estrutura típica SimpleJWT; nomes exatos podem variar conforme `SIMPLE_JWT` em `settings`)

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 5.2 Renovar access — `POST /api/usuarios/login/refresh/`

**Request**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response `200 OK`**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 5.3 Cadastrar representante — `POST /api/usuarios/cadastro/`

Chamado por um **gestor de Vendas** (ou superusuário). Campos conforme **`CadastroUsuarioSerializer`** (`serializers.py`).

**Request** (campos obrigatórios: `email`, `nome`, `tipo`, `password`, `password_confirm`; demais opcionais)

```json
{
  "email": "representante.sul@empresa.com.br",
  "nome": "Maria Representante",
  "tipo": "REPRESENTANTE",
  "password": "OutraSenhaForte456!",
  "password_confirm": "OutraSenhaForte456!",
  "telefone_contato": "(41) 99999-0000",
  "regiao_atuacao": "Paraná / Santa Catarina",
  "limite_desconto_maximo": "5.00",
  "meta_mensal": "50000.00",
  "percentual_comissao": "2.50"
}
```

**Response `201 Created`** (corpo fixo da view)

```json
{
  "mensagem": "Usuário criado!",
  "email": "representante.sul@empresa.com.br"
}
```

**Response `400 Bad Request`** — exemplo (validação de unicidade de e-mail)

```json
{
  "email": [
    "Este e-mail já está cadastrado em nosso sistema."
  ]
}
```

**Response `400 Bad Request`** — exemplo (senhas divergentes)

```json
{
  "password": "As senhas informadas não conferem."
}
```

### 5.4 Cadastrar gestor — mesmo endpoint (**somente superusuário**)

No MVP, **`tipo: "GESTOR"`** no `POST /cadastro/` é aceito **apenas** com autenticação de **`is_superuser`**. Gestores de Vendas ou de Logística recebem **`403 Forbidden`** se tentarem criar um gestor.

Campos de perfil de gestor no serializer: `departamento` (`VENDAS` | `LOGISTICA`), `ramal_interno` (opcional; vazio vira `'0000'` no serviço; `departamento` omitido defaulta a `VENDAS` no serviço).

**Request**

```json
{
  "email": "novo.gestor.logistica@empresa.com.br",
  "nome": "Gestor Logística",
  "tipo": "GESTOR",
  "password": "SenhaForte789!",
  "password_confirm": "SenhaForte789!",
  "departamento": "LOGISTICA",
  "ramal_interno": "2104"
}
```

**Response `201 Created`** (igual à view de cadastro)

```json
{
  "mensagem": "Usuário criado!",
  "email": "novo.gestor.logistica@empresa.com.br"
}
```

### 5.5 Leitura de usuário — `GET /api/usuarios/usuarios/{id}/`

**Response `200 OK`** (exemplo; **`password`** nunca aparece)

```json
{
  "id": 42,
  "username": "representante.sul",
  "email": "representante.sul@empresa.com.br",
  "tipo": "REPRESENTANTE"
}
```

### 5.6 Atualização parcial com troca de senha — `PATCH /api/usuarios/usuarios/{id}/`

**Request** (apenas campos desejados; exige permissão logística ou superusuário)

```json
{
  "email": "representante.sul.novo@empresa.com.br",
  "password": "NovaSenhaSegura2026!"
}
```

**Response `200 OK`:** objeto usuário atualizado (sem `password`).

---

## Apêndice: arquivos relacionados

| Arquivo | Conteúdo principal |
|---------|---------------------|
| `usuarios/models.py` | Entidades de domínio |
| `usuarios/serializers.py` | Contratos JSON |
| `usuarios/services.py` | `criar_usuario_com_perfil` |
| `usuarios/views.py` | HTTP + soft-delete + bloqueio `POST` |
| `usuarios/permissions.py` | Políticas DRF |
| `usuarios/urls.py` | Rotas |
| `setup/settings.py` | `AUTH_USER_MODEL`, `REST_FRAMEWORK`, `SIMPLE_JWT` |
