# Módulo `catalogo` — Referência técnica

Documentação de referência para **desenvolvedores backend**, **integração de APIs** e **frontends** que consomem categorias e produtos da distribuidora.

**Contratos globais**

| Item | Valor |
|------|--------|
| **Prefixo HTTP** | `/api/catalogo/` (`setup/urls.py` → `catalogo.urls`) |
| **App name (URL namespace)** | `catalogo` (`app_name` em `catalogo/urls.py`) |
| **Formato de corpo** | `application/json` |

---

## 1. Visão geral e arquitetura

### 1.1 Papel do módulo

O app `catalogo` é a **fonte centralizada** de:

- **Categorias** de produto (agrupamento lógico, texto descritivo opcional).
- **Produtos** (SKU único, preço base, estoque, vínculo obrigatório com uma categoria).

Não há **exclusão física** nas operações de API descritas aqui: remoções usam **soft-delete** (`ativo=False`), mantendo histórico e integridade referencial.

### 1.2 Camadas

```
Cliente (JSON)
    → CategoriaViewSet / ProdutoViewSet
        → CategoriaSerializer / ProdutoSerializer
        → Modelos Categoria, Produto (core.BaseModel)
```

| Camada | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **Rotas** | `catalogo/urls.py` | `DefaultRouter`: `categorias/`, `produtos/` |
| **Views** | `catalogo/views.py` | `ModelViewSet`, queryset `ativo=True`, `perform_destroy` soft |
| **Serialização** | `catalogo/serializers.py` | Campos expostos na API |
| **Autorização** | `catalogo/permissions.py` | `IsGestorVendasOrReadOnly` |
| **Modelagem** | `catalogo/models.py` | Entidades + `MinValueValidator` em `preco_base` |

### 1.3 Herança de modelo (`BaseModel`)

`Categoria` e `Produto` herdam de **`core.models.BaseModel`**:

| Campo | Tipo | Observação |
|-------|------|------------|
| `criado_em` | `DateTimeField` | `auto_now_add=True` |
| `atualizado_em` | `DateTimeField` | `auto_now=True` |
| `ativo` | `BooleanField` | Default `True`; usado para soft-delete e filtros de listagem |

### 1.4 Relacionamento produto ↔ categoria

- **`Produto.categoria`**: `ForeignKey(Categoria, on_delete=models.PROTECT, related_name='produtos')`.
- **`PROTECT`** impede **apagar** uma categoria no **ORM** enquanto existirem produtos apontando para ela (hard delete). Na prática, o fluxo de API usa **soft-delete** na categoria; produtos inativos não aparecem nas listagens padrão, mas registros antigos podem ainda referenciar a categoria — tratar conforme política de dados do produto.

---

## 2. Regras de negócio

### 2.1 Catálogo centralizado e ausência de deleção física pela API

- **Criação e edição** de categorias e produtos ocorrem pelos endpoints REST usuais (`POST`, `PUT`, `PATCH`).
- **`DELETE`** nos ViewSets **não** remove a linha: **`perform_destroy`** define apenas **`ativo=False`** e persiste (soft-delete).
- **Listagens** (`list`) e o queryset base dos ViewSets usam **`.filter(ativo=True)`**, portanto:
  - **Categorias inativas** não aparecem em `GET /categorias/`.
  - **Produtos inativos** não aparecem em `GET /produtos/`.
- **`retrieve` por PK** em registro com `ativo=False`: o objeto **não** está no queryset do ViewSet; a API tende a responder **`404 Not Found`** (comportamento padrão DRF ao não encontrar o objeto na coleção visível).

### 2.2 Integridade de preço (`preco_base`)

No modelo **`Produto`**:

```python
validators=[MinValueValidator(0.01)]
```

**Regra:** o preço base deve ser **estritamente positivo** — o valor mínimo aceito é **0,01** (na escala `max_digits=10`, `decimal_places=2`). Valores `0` ou negativos falham na validação do Django/DRF em criação ou atualização.

### 2.3 Campos dos serializers (contrato da API)

**`CategoriaSerializer`**: `id`, `nome`, `descricao`, `ativo`

**`ProdutoSerializer`**: `id`, `nome`, `sku`, `categoria` (PK da categoria), `preco_base`, `quantidade_estoque`, `ativo`

- **`quantidade_estoque`**: inteiro; default no modelo `0` se omitido em criação.
- **`sku`**: único globalmente no modelo; tentativa de duplicidade gera erro de validação/integridade.

---

## 3. Segurança e permissões

### 3.1 Classe `IsGestorVendasOrReadOnly`

Implementação em `catalogo/permissions.py`:

| Condição | Comportamento |
|----------|----------------|
| Não autenticado | **Negado** (`401` após autenticação JWT, conforme configuração DRF) |
| `GET`, `HEAD`, `OPTIONS` (`SAFE_METHODS`) | **Permitido** para qualquer usuário autenticado |
| `POST`, `PUT`, `PATCH`, `DELETE` | **Permitido** apenas se **`request.user.is_superuser`** **ou** (`tipo == 'GESTOR'` **e** `request.user.perfil_gestor.departamento == 'VENDAS'`) |
| Gestor sem `perfil_gestor` acessível | Escrita **negada** (`403`) |
| **`REPRESENTANTE`** | Apenas **leitura**; qualquer escrita → **`403 Forbidden`** |

**Resumo:** escrita no catálogo é de **Vendas** (ou superusuário); **representantes** usam o catálogo em modo **somente leitura**.

### 3.2 Cabeçalho JWT

Para qualquer rota do catálogo (incluindo `GET`):

```http
Authorization: Bearer <access_token>
```

---

## 4. Endpoints (rotas)

Substitua `{id}` pelo identificador numérico retornado pela API.

### 4.1 Categorias

| Método | Caminho completo | Descrição |
|--------|------------------|-----------|
| `GET` | `/api/catalogo/categorias/` | Lista categorias **ativas** |
| `POST` | `/api/catalogo/categorias/` | Cria categoria (permissão Vendas / superuser) |
| `GET` | `/api/catalogo/categorias/{id}/` | Detalhe (se ativa e visível ao queryset) |
| `PUT` | `/api/catalogo/categorias/{id}/` | Substituição completa |
| `PATCH` | `/api/catalogo/categorias/{id}/` | Atualização parcial |
| `DELETE` | `/api/catalogo/categorias/{id}/` | Soft-delete (`ativo=False`) |

### 4.2 Produtos

| Método | Caminho completo | Descrição |
|--------|------------------|-----------|
| `GET` | `/api/catalogo/produtos/` | Lista produtos **ativos** |
| `POST` | `/api/catalogo/produtos/` | Cria produto |
| `GET` | `/api/catalogo/produtos/{id}/` | Detalhe |
| `PUT` | `/api/catalogo/produtos/{id}/` | Substituição completa |
| `PATCH` | `/api/catalogo/produtos/{id}/` | Atualização parcial |
| `DELETE` | `/api/catalogo/produtos/{id}/` | Soft-delete (`ativo=False`) |

### 4.3 Códigos HTTP frequentes

| Código | Contexto |
|--------|----------|
| `200` | `GET`, `PUT`, `PATCH` com sucesso |
| `201` | `POST` com sucesso |
| `204` | `DELETE` com sucesso (comum em DRF) |
| `400` | Payload inválido (ex.: preço abaixo de 0,01) |
| `401` | Não autenticado |
| `403` | Autenticado sem permissão de escrita |
| `404` | Recurso inexistente ou inativo (fora do queryset) |

---

## 5. Exemplos de uso (JSON)

Ordem recomendada para integração: **criar categoria** → obter **`id`** → **criar produto** com `categoria` = esse id.

### 5.1 Criar categoria — `POST /api/catalogo/categorias/`

**Headers**

```http
POST /api/catalogo/categorias/ HTTP/1.1
Host: <host>
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request**

```json
{
  "nome": "Bebidas",
  "descricao": "Refrigerantes, sucos e água.",
  "ativo": true
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "nome": "Bebidas",
  "descricao": "Refrigerantes, sucos e água.",
  "ativo": true
}
```

**Notas**

- `descricao` pode ser omitida (`null` permitido no modelo) ou string vazia, conforme política do frontend.
- `ativo` pode ser omitido: o modelo default é `True`; enviar explicitamente evita ambiguidade em clientes gerados.

### 5.2 Criar produto vinculado à categoria — `POST /api/catalogo/produtos/`

Use o **`id`** da categoria retornado no passo anterior (`1` neste exemplo).

**Request**

```json
{
  "nome": "Refrigerante Cola 2L",
  "sku": "BEV-COLA-2L-001",
  "categoria": 1,
  "preco_base": "8.99",
  "quantidade_estoque": 120,
  "ativo": true
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "nome": "Refrigerante Cola 2L",
  "sku": "BEV-COLA-2L-001",
  "categoria": 1,
  "preco_base": "8.99",
  "quantidade_estoque": 120,
  "ativo": true
}
```

**Response `400 Bad Request`** — exemplo (preço inválido: zero ou negativo)

```json
{
  "preco_base": [
    "Certifique-se de que este valor seja maior ou igual a 0.01."
  ]
}
```

(A mensagem exata pode variar conforme locale/versão do Django; o validador no modelo é `MinValueValidator(0.01)`.)

### 5.3 Listagem (representante) — `GET /api/catalogo/produtos/`

**Response `200 OK`** (estrutura paginada ou lista simples depende de `REST_FRAMEWORK` em `settings`; exemplo sem paginação)

```json
[
  {
    "id": 1,
    "nome": "Refrigerante Cola 2L",
    "sku": "BEV-COLA-2L-001",
    "categoria": 1,
    "preco_base": "8.99",
    "quantidade_estoque": 120,
    "ativo": true
  }
]
```

### 5.4 Soft-delete — `DELETE /api/catalogo/produtos/{id}/`

Após sucesso, o registro deixa de aparecer em `GET /api/catalogo/produtos/`. Corpo vazio com **`204 No Content`** é o comportamento usual do `destroy` do DRF.

---

## Apêndice: referência rápida de arquivos

| Arquivo | Responsabilidade |
|---------|------------------|
| `catalogo/models.py` | `Categoria`, `Produto`, validador de preço |
| `catalogo/serializers.py` | Contratos JSON |
| `catalogo/views.py` | ViewSets + soft-delete |
| `catalogo/permissions.py` | `IsGestorVendasOrReadOnly` |
| `catalogo/urls.py` | Registro de rotas |
| `core/models.py` | `BaseModel` (`criado_em`, `atualizado_em`, `ativo`) |
