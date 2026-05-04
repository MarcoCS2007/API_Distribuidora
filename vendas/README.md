# Motor de Pedidos (MVP) — App `vendas`

Este documento descreve, de forma completa e orientada a integrações, o **motor de pedidos** do MVP (app Django/DRF `vendas`). O objetivo é servir como **referência para o frontend** e para qualquer consumidor da API.

---

## 1. Visão Geral e Arquitetura

### 1.1. Onde o módulo se encaixa

- **Projeto Django**: `setup`
- **App de pedidos**: `vendas`
- **Integração com outras apps**:
  - `usuarios`: identifica o **Representante logado** (via `request.user.perfil_representante`) e contém o campo de **limite de desconto**.
  - `catalogo`: fornece o `Produto` e seu `preco_base` (usado na regra de “fotografia de preço”).

### 1.2. Componentes principais (camadas)

- **Modelos (`vendas/models.py`)**
  - `Pedido`: “capa” do pedido (cliente, status, total, observações).
  - `ItemPedido`: itens do pedido (produto, quantidade, preço aplicado, desconto, subtotal).

- **Serializers (`vendas/serializers.py`)**
  - `PedidoSerializer`: faz **validações de negócio** e implementa a **criação aninhada (nested)** com cálculo automático e transação atômica.
  - `ItemPedidoSerializer`: expõe o item; campos de cálculo são **somente leitura**.

- **ViewSet (`vendas/views.py`)**
  - `PedidoViewSet` (DRF `ModelViewSet`): fornece CRUD de `Pedido` e implementa:
    - **Proteção contra IDOR** no `get_queryset` (escopo do representante).
    - **Cancelamento lógico** no `perform_destroy` (DELETE não apaga, apenas muda status para `CANCELADO`).

- **Permissões (`vendas/permissions.py`)**
  - `AcessoVendas`: exige autenticação e impõe regras por tipo de usuário e por status do pedido.

### 1.3. Base URL

O app `vendas` está montado em:

- `api/vendas/` (em `setup/urls.py`)
- rotas do ViewSet: `pedidos/` (em `vendas/urls.py` via `DefaultRouter`)

Em integrações, considere a base:

- **Base**: `/api/vendas/`
- **Recurso**: `/api/vendas/pedidos/`

---

## 2. Regras de Negócio e Cálculos

As regras abaixo são implementadas no serializer `PedidoSerializer` e no modelo `ItemPedido`.

### 2.1. Criação Aninhada (Nested) com integridade

- O endpoint de criação de pedido recebe, no **mesmo JSON**, os dados de `Pedido` e uma lista `itens` contendo os `ItemPedido`.
- A criação é executada dentro de uma **transação atômica** (`@transaction.atomic`).
  - Se qualquer item falhar (ex.: desconto acima do permitido), **nada é persistido**.

**Implicação para o frontend**

- O frontend deve enviar **apenas dados de entrada**, sem campos calculados.
- O backend retorna o pedido com os cálculos aplicados e IDs gerados.

### 2.2. Fotografia de Preço (price snapshot)

- No momento da criação do pedido, o backend **busca o preço atual** do produto no catálogo (`Produto.preco_base`).
- Esse valor é **congelado** no item, no campo `preco_unitario_aplicado`.
- O histórico do pedido fica **blindado** contra mudanças futuras no catálogo.

**O que o frontend envia**

- O frontend **não envia** preço por item.
- O frontend envia apenas o `produto` (ID) e o backend resolve o preço no banco.

**Onde isso acontece**

- Dentro do `PedidoSerializer.create()`, para cada item:
  - `preco_aplicado = produto.preco_base`
  - salva em `ItemPedido.preco_unitario_aplicado`

### 2.3. Cálculos automáticos (sem subtotal/total no request)

O frontend **não deve** enviar `subtotal` nem `valor_total`. O backend calcula durante a criação.

#### 2.3.1. Fórmulas aplicadas por item

Para cada `ItemPedido`, o backend calcula:

- **Valor bruto**: \(valor\_bruto = preco\_unitario\_aplicado \times quantidade\)
- **Valor de desconto**: \(valor\_desconto = valor\_bruto \times (desconto\_percentual/100)\)
- **Subtotal**: \(subtotal = valor\_bruto - valor\_desconto\)

Observações importantes:

- O serializer faz cast de `desconto_percentual` para `Decimal` para evitar imprecisão:
  - `Decimal(str(desconto)) / Decimal('100')`
- O `Pedido.valor_total` é a soma dos subtotais de todos os itens.

#### 2.3.2. Campos calculados e somente leitura

O backend expõe (e controla) os campos calculados:

- Em `ItemPedido`:
  - `preco_unitario_aplicado`: **read-only**
  - `subtotal`: **read-only**
- Em `Pedido`:
  - `representante`: **read-only** (vem do usuário logado)
  - `valor_total`: **read-only**
  - `status`: **read-only** (no MVP, inicia como `EM_DIGITACAO`)

Se o frontend enviar esses campos, eles **não devem** ser considerados como fonte de verdade; o backend persiste os seus próprios valores.

### 2.4. Trava de Desconto (validação por perfil do Representante)

O MVP implementa uma trava rígida de desconto **linha a linha**, validando cada item contra o limite máximo do representante logado.

- O backend obtém:
  - `representante = request.user.perfil_representante`
  - `limite_desconto = representante.limite_desconto_maximo`
- Para cada item do request:
  - se `desconto_percentual > limite_desconto`, o backend retorna **HTTP 400** com mensagem de bloqueio.

**Importante**

- A validação ocorre no `PedidoSerializer.validate()`, antes de qualquer persistência.
- Se o usuário autenticado **não** possui `perfil_representante`, a API retorna erro de validação informando que apenas representantes podem emitir pedidos.

### 2.5. Pedido não pode ser vazio

Na criação:

- `itens` é obrigatório e deve conter **pelo menos um item**.
- Caso contrário, a API retorna **HTTP 400** com:
  - `{"itens": "O pedido deve conter pelo menos um item."}`

### 2.6. Status do Pedido (ciclo no MVP)

O modelo `Pedido` possui:

- `EM_DIGITACAO`: rascunho (default).
- `FINALIZADO`: fechado e pronto para envio/faturamento.
- `CANCELADO`: cancelamento lógico (histórico preservado).

No MVP atual:

- Ao criar, o pedido inicia como **`EM_DIGITACAO`**.
- O endpoint DELETE **não apaga**: muda para **`CANCELADO`**.
- Regras de permissão impedem que representantes alterem/excluam pedidos que **não** estejam em `EM_DIGITACAO`.

---

## 3. Segurança e Permissões

O módulo aplica segurança em duas camadas:

- **Escopo de consulta (IDOR)**: `get_queryset()` restringe quais pedidos aparecem em listagens/consultas.
- **Permissão por objeto**: `has_object_permission()` valida acesso a um pedido específico (incluindo regras por método HTTP e status).

### 3.1. Autenticação

Todas as rotas exigem usuário autenticado:

- `AcessoVendas.has_permission()` retorna `request.user.is_authenticated`.

### 3.2. Proteção IDOR no `get_queryset` (escopo por usuário)

Implementação em `PedidoViewSet.get_queryset()`:

- Se não autenticado: retorna `Pedido.objects.none()`.
- Se `is_superuser`: vê todos os pedidos.
- Se `user.tipo == 'REPRESENTANTE'`: retorna **somente** pedidos do próprio representante:
  - `qs.filter(representante__usuario=user)`
- Se `user.tipo == 'GESTOR'`:
  - Se o gestor for do departamento `LOGISTICA`: retorna apenas pedidos `FINALIZADO`.
  - Caso contrário (ex.: Vendas): vê o panorama geral (`qs`).
- Outros tipos: não vê nada.

**Por que isso é crítico**

- Mesmo que o frontend tente acessar um `id` de pedido que não pertence ao representante, o pedido não aparecerá no queryset da listagem e, combinado com a permissão de objeto, impede exploração típica de IDOR.

### 3.3. Permissão por objeto (regras por tipo e método)

Implementação em `AcessoVendas.has_object_permission()`:

#### 3.3.1. Admin (`is_superuser`)

- Acesso total: `True` para qualquer método.

#### 3.3.2. Representante (`user.tipo == 'REPRESENTANTE'`)

- **Escopo**: o pedido deve ser do próprio representante:
  - Se `obj.representante.usuario != request.user` → `False`
- **Rascunho obrigatório para mutações**:
  - Se o método **não** for seguro (POST/PUT/PATCH/DELETE) e `obj.status != 'EM_DIGITACAO'` → `False`
- Caso contrário: `True`

Em termos práticos:

- Pode **listar/consultar** seus pedidos.
- Pode **alterar/cancelar** apenas pedidos em `EM_DIGITACAO`.
- Não pode alterar/cancelar pedidos `FINALIZADO` ou `CANCELADO`.

#### 3.3.3. Gestor (`user.tipo == 'GESTOR'`)

- No MVP, gestores têm **apenas leitura**:
  - Se método em `SAFE_METHODS` (GET/HEAD/OPTIONS) → pode, com restrições.
  - Métodos não seguros → `False`.
- Restrição extra para Logística:
  - Se `perfil_gestor.departamento == 'LOGISTICA'` → só pode ler pedidos com `status == 'FINALIZADO'`.
- Gestor de Vendas (não Logística): pode ler tudo.

### 3.4. Cancelamento lógico (DELETE sobrescrito)

O endpoint DELETE (`destroy`) não remove o registro no banco.

- Implementação: `PedidoViewSet.perform_destroy()`
- Comportamento:
  - `instance.status = 'CANCELADO'`
  - `instance.save()`

**Impacto para integrações**

- DELETE retorna sucesso (comportamento padrão do DRF), mas o pedido permanece persistido.
- O frontend deve tratar “remoção” como **cancelamento** e refletir o status `CANCELADO` nas telas.

---

## 4. Endpoints (com tabelas de rotas)

As rotas são geradas por `DefaultRouter` registrando `PedidoViewSet` no prefixo `pedidos`.

### 4.1. Tabela de rotas do recurso `Pedido`

Base: `/api/vendas/pedidos/`

| Método | Rota | Ação DRF | Descrição | Permissão (resumo) |
|---|---|---|---|---|
| GET | `/api/vendas/pedidos/` | `list` | Lista pedidos no escopo do usuário | Autenticado; representante vê só os seus; gestor conforme regras; admin vê tudo |
| POST | `/api/vendas/pedidos/` | `create` | Cria pedido com itens (nested) e cálculos automáticos | Requer `perfil_representante`; valida desconto e itens |
| GET | `/api/vendas/pedidos/{id}/` | `retrieve` | Detalha um pedido | Representante só do próprio pedido; gestor somente leitura; logística só `FINALIZADO` |
| PUT | `/api/vendas/pedidos/{id}/` | `update` | Atualiza pedido (DRF padrão) | Representante apenas se `EM_DIGITACAO` e dono; gestor não altera; admin altera |
| PATCH | `/api/vendas/pedidos/{id}/` | `partial_update` | Atualiza parcial | Mesmas regras do PUT |
| DELETE | `/api/vendas/pedidos/{id}/` | `destroy` | **Cancela** (status → `CANCELADO`) | Representante apenas se `EM_DIGITACAO` e dono; gestor não cancela; admin pode |

### 4.2. Observações sobre payloads e campos

#### 4.2.0. Limitação do MVP: atualização aninhada de `itens`

O serializer atual implementa **criação** aninhada (`create()`), porém **não** implementa `update()` customizado para atualização de `itens`.

Implicações práticas:

- **POST** com `itens` é suportado e é o fluxo principal do MVP.
- **PUT/PATCH**:
  - Atualizações simples de campos da “capa” (ex.: `cliente_nome`, `cliente_cnpj`, `observacoes`) tendem a ser o uso esperado.
  - Atualizar `itens` (adicionar/remover/alterar itens) **não é um fluxo garantido** no MVP, pois o DRF não faz atualização nested automaticamente sem lógica explícita.

Recomendação para integrações de frontend:

- Trate `itens` como **imutáveis após a criação** no MVP (a menos que o backend evolua para suportar update nested).
- Para “editar itens”, a estratégia típica é **cancelar** o rascunho e criar um novo pedido.

#### 4.2.1. Campos do Pedido (entrada vs saída)

- **Entrada esperada no POST**:
  - `cliente_nome` (string)
  - `cliente_cnpj` (string)
  - `observacoes` (string opcional)
  - `itens` (array obrigatório)
- **Campos controlados pelo backend** (não enviar / ignorar no request):
  - `representante`
  - `status`
  - `valor_total`
  - `criado_em`

#### 4.2.2. Campos do ItemPedido (entrada vs saída)

- **Entrada esperada**:
  - `produto` (ID do produto)
  - `quantidade` (inteiro positivo)
  - `desconto_percentual` (decimal, opcional; default 0)
- **Campos calculados (read-only)**:
  - `preco_unitario_aplicado`
  - `subtotal`
- Campo adicional na saída:
  - `produto_nome` (somente leitura; `produto.nome`)

---

## 5. Exemplos de Uso (Payloads JSON de Request e Response)

Os exemplos abaixo seguem o comportamento real do serializer e do ViewSet do MVP.

### 5.1. Criar pedido (POST `/api/vendas/pedidos/`)

#### 5.1.1. Request (frontend → backend)

Repare que:

- O frontend envia `itens` no mesmo JSON (nested).
- O frontend **não envia** `valor_total`, `subtotal` nem `preco_unitario_aplicado`.
- Cada item contém `produto`, `quantidade`, `desconto_percentual`.

```json
{
  "cliente_nome": "Mercado Central LTDA",
  "cliente_cnpj": "12.345.678/0001-90",
  "observacoes": "Entregar no período da manhã.",
  "itens": [
    {
      "produto": 10,
      "quantidade": 3,
      "desconto_percentual": "5.00"
    },
    {
      "produto": 25,
      "quantidade": 1,
      "desconto_percentual": "0.00"
    }
  ]
}
```

#### 5.1.2. Response de sucesso (backend → frontend) — HTTP 201

Repare que o backend devolve:

- `representante` e `representante_nome` preenchidos com base no usuário logado.
- `status` iniciado em `EM_DIGITACAO`.
- `preco_unitario_aplicado` congelado a partir de `Produto.preco_base`.
- `subtotal` calculado por item.
- `valor_total` somado a partir dos subtotais.

```json
{
  "id": 123,
  "representante": 7,
  "representante_nome": "Marco Silva",
  "cliente_nome": "Mercado Central LTDA",
  "cliente_cnpj": "12.345.678/0001-90",
  "status": "EM_DIGITACAO",
  "valor_total": "284.05",
  "observacoes": "Entregar no período da manhã.",
  "criado_em": "2026-05-04T15:10:00-03:00",
  "itens": [
    {
      "id": 1001,
      "produto": 10,
      "produto_nome": "Refrigerante 2L",
      "quantidade": 3,
      "preco_unitario_aplicado": "49.90",
      "desconto_percentual": "5.00",
      "subtotal": "142.22"
    },
    {
      "id": 1002,
      "produto": 25,
      "produto_nome": "Água Mineral 500ml",
      "quantidade": 1,
      "preco_unitario_aplicado": "149.80",
      "desconto_percentual": "0.00",
      "subtotal": "149.80"
    }
  ]
}
```

> Os valores acima são ilustrativos; o que importa é a **forma** da resposta e o fato de os cálculos virem do backend.

### 5.2. Erro de desconto acima do limite (POST `/api/vendas/pedidos/`) — HTTP 400

Se algum item vier com `desconto_percentual` maior que `request.user.perfil_representante.limite_desconto_maximo`, o serializer bloqueia.

#### 5.2.1. Request (exemplo)

```json
{
  "cliente_nome": "Mercado Central LTDA",
  "cliente_cnpj": "12.345.678/0001-90",
  "itens": [
    {
      "produto": 10,
      "quantidade": 3,
      "desconto_percentual": "30.00"
    }
  ]
}
```

#### 5.2.2. Response (exemplo) — HTTP 400

```json
{
  "desconto_percentual": "Desconto de 30.00% bloqueado. Seu limite máximo é 10.00%."
}
```

### 5.3. Cancelar pedido (DELETE `/api/vendas/pedidos/{id}/`)

- Representante só consegue cancelar se:
  - o pedido for dele, e
  - o status estiver em `EM_DIGITACAO`.
- O backend não apaga: muda `status` para `CANCELADO`.

Após o DELETE, ao consultar o pedido (`GET /api/vendas/pedidos/{id}/`), espere ver:

```json
{
  "id": 123,
  "status": "CANCELADO"
}
```

