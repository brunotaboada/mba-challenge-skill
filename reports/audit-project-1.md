================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-05-14

## Phase 1 — Project Analysis

```
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários, itens_pedido)
Architecture:  Monolítica — 4 arquivos no root, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
```

Endpoints detectados:
- `GET    /`, `GET /health`
- `GET    /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`
- `POST   /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`
- `GET    /usuarios`, `GET /usuarios/<id>`, `POST /usuarios`, `POST /login`
- `POST   /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`
- `GET    /relatorios/vendas`
- `POST   /admin/reset-db`, `POST /admin/query`

## Summary

| Severidade | Quantidade |
|---|---|
| CRITICAL | 9 |
| HIGH     | 5 |
| MEDIUM   | 4 |
| LOW      | 3 |
| **Total**| **21** |

Critical-or-High count: 14 (≥1 required by acceptance criteria) ✓

## Findings

### [CRITICAL] Hardcoded Secret  (AP-001)
File: `app.py:7`
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` definido como literal no código fonte.
Impact: Segredo no histórico do Git é vazamento permanente; permite assinar/forjar tokens.
Recommendation: T-001 — mover para `os.environ.get("SECRET_KEY")`, fornecer `.env.example`, não commitar `.env`.

### [CRITICAL] DEBUG=True em produção  (AP-107)
File: `app.py:8`, `app.py:88`
Description: `app.config["DEBUG"] = True` no código + `app.run(debug=True)`.
Impact: Stack trace + console interativo de execução expostos a qualquer cliente que cause exceção.
Recommendation: T-001 — ler de env (`FLASK_DEBUG`).

### [CRITICAL] CORS totalmente aberto  (AP-107)
File: `app.py:9`
Description: `CORS(app)` sem parâmetro `origins=...`.
Impact: Qualquer origem na web faz fetch autenticado contra a API.
Recommendation: T-001 — `CORS(app, origins=settings.ALLOWED_ORIGINS)`.

### [CRITICAL] Endpoint executa SQL arbitrário sem auth  (AP-005)
File: `app.py:59-78`
Description: `POST /admin/query` aceita campo `sql` no body e executa direto: `cursor.execute(query)`. Sem autenticação, role check, ou whitelist.
Impact: SQLi-as-a-service — qualquer ator dump/drop o banco.
Recommendation: Remover o endpoint. Operações de manutenção devem ser comandos CLI, não rotas HTTP.

### [CRITICAL] DB-wipe sem autenticação  (AP-005)
File: `app.py:47-57`
Description: `POST /admin/reset-db` apaga `itens_pedido`, `pedidos`, `produtos`, `usuarios` sequencialmente. Sem auth.
Impact: Qualquer ator com a URL apaga o banco inteiro.
Recommendation: Remover o endpoint; reset apenas via comando administrativo em ambiente.

### [CRITICAL] SQL Injection sistêmica  (AP-002)
File: `models.py:28, 47-50, 57-61, 68, 92, 109-110, 127-128, 140, 148-150, 155, 157-160, 163-165, 174, 188, 192, 206, 220, 224, 280-281, 289-298`
Description: Quase toda função em `models.py` monta SQL com `+ str(...)` ou `"'" + var + "'"`. Caso mais crítico: `login_usuario` em linhas 109-110 — `SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'`.
Impact: Bypass de login trivial com `admin' OR '1'='1`; leitura de qualquer tabela; potencial drop.
Recommendation: T-002 — parametrizar **todas** as queries. Exemplo: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

### [CRITICAL] Senhas em plaintext no banco  (AP-003)
File: `database.py:30-37` (schema sem hash), `database.py:73-77` (seed com `"admin/admin123"`, `"123456"`, `"senha123"`), `models.py:127-128` (INSERT com senha pura)
Description: Coluna `usuarios.senha TEXT` sem hash; seeds populam senhas em plaintext; comparação direta em `login_usuario`.
Impact: Vazamento do `loja.db` = vazamento direto de credenciais.
Recommendation: T-003 — armazenar `bcrypt.hashpw(...)`; substituir comparação por `bcrypt.checkpw(...)`.

### [CRITICAL] Senhas vazadas na resposta da API  (AP-004)
File: `models.py:79-87` (`get_todos_usuarios`), `models.py:94-103` (`get_usuario_por_id`)
Description: Funções retornam o campo `senha` no dict que vira JSON da API em `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Listar usuários expõe credenciais.
Recommendation: T-004 — remover `senha` do `to_dict()`/dict serializado.

### [CRITICAL] Segredos expostos no /health  (AP-004)
File: `controllers.py:285-290`
Description: Health check responde com `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True`.
Impact: Qualquer cliente recupera o SECRET_KEY.
Recommendation: T-004 — health retorna apenas `{status, version, db_connected}`.

### [HIGH] God Module — models.py  (AP-101)
File: `models.py:1-314`
Description: Arquivo único contém DAO de 4 entidades (produto, usuário, pedido, item_pedido) + regra de criação de pedido (decremento de estoque, validação) + agregação do relatório de vendas + tabela de desconto.
Impact: Impossível testar em isolamento; qualquer alteração afeta tudo; merge conflicts contínuos.
Recommendation: T-005 — separar em `src/models/{produto,usuario,pedido}.py` + `src/services/pedido_service.py` + `src/services/relatorio_service.py`.

### [HIGH] Conexão global mutável  (AP-102)
File: `database.py:4-9`
Description: `db_connection = None` é variável de módulo reatribuída no `get_db()`; conexão singleton + `check_same_thread=False` na linha 11.
Impact: Race conditions sob carga concorrente (Flask dev server); estado compartilhado entre requests.
Recommendation: Usar `flask.g` ou factory de conexão request-scoped; remover global.

### [HIGH] Side-effects em controller (notificações falsas)  (AP-103)
File: `controllers.py:208-210, 248-251`
Description: `criar_pedido` e `atualizar_status_pedido` simulam envio de email/SMS/push com `print(...)` dentro do controller.
Impact: Lógica de notificação acoplada ao HTTP layer; impossível trocar provider ou desabilitar para teste.
Recommendation: T-005 — extrair `NotificationService` com injeção de dependência.

### [HIGH] Validação duplicada (DRY)  (AP-105)
File: `controllers.py:28-55` (criar_produto) ↔ `controllers.py:67-91` (atualizar_produto)
Description: Bloco de validação literal repetido entre criação e atualização de produto (campos obrigatórios, preço negativo, estoque negativo, categorias válidas).
Impact: Alterar regra requer mudar nos dois lugares; fácil ficar fora de sincronia.
Recommendation: T-005 — extrair `validate_produto_payload(data, partial: bool)` em `utils/validators.py`.

### [HIGH] Operação multi-step sem transação  (AP-104)
File: `models.py:148-169`
Description: `criar_pedido` faz INSERT em `pedidos`, N INSERTs em `itens_pedido` e N UPDATEs em `produtos` (decremento de estoque) sem `BEGIN TRANSACTION`. Falha no meio deixa banco inconsistente.
Impact: Pedido com itens parciais; estoque decrementado de produtos que não foram inseridos no pedido.
Recommendation: T-006 — `cursor.execute("BEGIN")` + try/except com `ROLLBACK`.

### [MEDIUM] N+1 query em listagem de pedidos  (AP-201)
File: `models.py:186-200` (`get_pedidos_usuario`), `models.py:217-232` (`get_todos_pedidos`)
Description: Para cada pedido, abre `cursor2` para buscar itens; para cada item, abre `cursor3` para buscar nome do produto. Cardinalidade O(P · I · 2).
Impact: 100 pedidos × 3 itens = 700 queries para listar.
Recommendation: T-007 — JOIN único entre `pedidos`, `itens_pedido` e `produtos`.

### [MEDIUM] Regra de negócio com magic numbers  (AP-203)
File: `models.py:256-262`
Description: Tabela de desconto inline: `> 10000 → 10%`, `> 5000 → 5%`, `> 1000 → 2%`. Misturada com o cálculo do relatório.
Impact: Mudança de regra exige varrer o módulo; sem auditoria de quando/por que mudou.
Recommendation: T-010 — extrair para `config/constants.py` ou para regra explícita em service.

### [MEDIUM] Lista de categorias hardcoded em controller  (AP-203)
File: `controllers.py:52`
Description: `categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]` inline.
Impact: Acrescentar categoria exige deploy de código.
Recommendation: T-010 — `Enum` ou tabela de configuração.

### [MEDIUM] Validação ausente — email no cadastro de usuário  (AP-202)
File: `controllers.py:146-165`
Description: `criar_usuario` aceita qualquer string como `email`. Sem regex, sem checagem de duplicidade.
Impact: Lixo no banco; dois usuários com mesmo email possíveis.
Recommendation: T-005 + schema com `marshmallow` ou regex centralizado em `utils/validators.py` + `UNIQUE` na coluna.

### [LOW] `print()` usado como logging  (AP-301)
File: `controllers.py:8, 11, 57, 61, 106, 179, 182, 208-210, 219, 248-251`
Description: 14 chamadas a `print()` para registrar fluxo de execução.
Impact: Sem níveis (DEBUG/INFO/WARN/ERROR); sem formato estruturado; sem controle de destino.
Recommendation: T-010 — `logging.getLogger(__name__)` configurado em `app.py`.

### [LOW] Mapeamento manual de Row → dict repetitivo  (AP-302)
File: `models.py:11-21, 30-41, 79-87, 95-103, 177-200, 209-232, 302-313`
Description: Mesmo padrão de `result.append({"id": row["id"], "nome": row["nome"], ...})` reescrito em 7 lugares.
Impact: 7 lugares para atualizar quando muda o schema; baixa hygiene.
Recommendation: Helper `row_to_dict(row, fields)` em `utils/` ou dict-comprehension uniforme.

### [LOW] Magic strings de status de pedido  (AP-303)
File: `controllers.py:242`, `models.py:280`
Description: Lista `["pendente", "aprovado", "enviado", "entregue", "cancelado"]` em um lugar; comparações com literais em outro.
Impact: Typo em literal não é detectado.
Recommendation: T-010 — `Enum` em `config/constants.py`.

## APIs Deprecated

Nenhuma API deprecated detectada neste projeto. O código usa APIs atuais do
Flask 3.1.1 e do `sqlite3` da stdlib. O risco maior está na ausência de hash
de senha, coberto em `AP-003`.

================================
Total: 21 findings
Summary: CRITICAL: 9 | HIGH: 5 | MEDIUM: 4 | LOW: 3
Critical-or-High count: 14   (≥1 required by acceptance criteria)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
