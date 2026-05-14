# Análise dos 3 Projetos Base — Insumo para a Skill `refactor-arch`

> Documento de trabalho. Catálogo todos os achados que encontrei lendo cada
> projeto, com arquivo + linhas exatas e severidade. É a fonte de verdade
> para (a) a seção "Análise Manual" do README, (b) o catálogo de
> anti-patterns da skill e (c) os 3 relatórios de auditoria.
>
> Base: <https://github.com/devfullcycle/mba-ia-refactor-projects-skill>

Escala de severidade (do enunciado):
- **CRITICAL** — falha grave de arquitetura/segurança; expõe dados; viola completamente SoC.
- **HIGH** — violação forte de MVC/SOLID; dificulta manutenção/testes; estado global mutável.
- **MEDIUM** — duplicação, performance moderada (N+1), validação ausente.
- **LOW** — legibilidade, naming, magic numbers.

---

## Projeto 1 — `code-smells-project` (Python / Flask 3.1.1)

**Domínio:** API de E-commerce (produtos, usuários, pedidos, itens_pedido, relatórios).
**Estrutura atual:** monolítica, 4 arquivos no root, sem camadas.
**Arquivos:** `app.py` (88), `controllers.py` (292), `database.py` (86), `models.py` (314) — ~780 LOC.
**Banco:** SQLite (`loja.db`) com 4 tabelas.

### Achados

| # | Severidade | Categoria | Arquivo:Linha | Descrição |
|---|---|---|---|---|
| 1 | CRITICAL | Hardcoded Secret | `app.py:7` | `SECRET_KEY = "minha-chave-super-secreta-123"` no código. |
| 2 | CRITICAL | Debug em produção | `app.py:8`, `app.py:88` | `DEBUG=True` + `app.run(debug=True)`. |
| 3 | CRITICAL | SQL Injection | `models.py:28,47-50,57-61,68,92,109-110,127-128,140,148-150,155,157-160,163-165,174,188-192,206,220-225,280-281,289-298` | Praticamente toda query usa concatenação de string com input do usuário. `login_usuario` é o caso clássico: `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`. |
| 4 | CRITICAL | SQL como serviço | `app.py:59-78` | Endpoint `/admin/query` executa SQL arbitrário do body. |
| 5 | CRITICAL | DB wipe sem auth | `app.py:47-57` | `/admin/reset-db` apaga todas as tabelas, sem autenticação. |
| 6 | CRITICAL | Senhas em plaintext | `database.py:30-37`, `models.py:127-128`, `seed` (`"admin/admin123"`) | Tabela `usuarios.senha TEXT` sem hash. |
| 7 | CRITICAL | Senha vazando na API | `models.py:79-87` (`get_todos_usuarios`), `models.py:94-103` (`get_usuario_por_id`) | Campo `senha` retornado no JSON da listagem/detalhe de usuários. |
| 8 | CRITICAL | Segredo no `/health` | `controllers.py:285-290` | Health check expõe `secret_key`, `db_path`, `debug`. |
| 9 | CRITICAL | CORS totalmente aberto | `app.py:9` | `CORS(app)` sem `origins`/whitelist. |
| 10 | HIGH | God Module | `models.py:1-314` | DAO + regra de negócio + lookup de preço + decremento de estoque + regra de desconto, tudo num único arquivo, sem camadas. |
| 11 | HIGH | Conexão global mutável | `database.py:4-9` | `db_connection` é variável de módulo + `check_same_thread=False` → race condition entre requests. |
| 12 | HIGH | Side-effects em controller | `controllers.py:208-210`, `controllers.py:248-251` | "Envio de email/SMS/push" simulado por `print` dentro do controller de pedidos. |
| 13 | HIGH | Validação duplicada | `controllers.py:28-55` ↔ `controllers.py:67-91` | `criar_produto` e `atualizar_produto` repetem validação literalmente. |
| 14 | HIGH | Falta de transação | `models.py:148-169` | `criar_pedido` faz N INSERTs + UPDATE em produtos sem `BEGIN/COMMIT` explícito; falha no meio deixa banco inconsistente. |
| 15 | MEDIUM | N+1 query | `models.py:171-201`, `models.py:203-233` | `get_pedidos_usuario`/`get_todos_pedidos` abrem cursores aninhados por item. |
| 16 | MEDIUM | Regra de negócio com magic numbers | `models.py:256-262` | Tabela de desconto (10000/5000/1000 → 10%/5%/2%) hardcoded no model. |
| 17 | MEDIUM | Categorias inline | `controllers.py:52` | Lista de categorias válidas hardcoded no controller. |
| 18 | MEDIUM | Validação ausente de email | `controllers.py:146-165` | `criar_usuario` não valida formato. |
| 19 | LOW | `print` como logging | `controllers.py:8,11,57,61,106,179,182,208-210,219,248-251` | Sem `logging` nem níveis. |
| 20 | LOW | Mapeamento manual repetitivo | `models.py:11-21,30-41,79-87,95-103,177-200,209-232,302-313` | `dict(row)` por mão em vez de helper. |
| 21 | LOW | Magic strings de status | `controllers.py:242`, `models.py:280` | Lista de status repetida; sem Enum. |

**Resumo:** 9 CRITICAL · 5 HIGH · 4 MEDIUM · 3 LOW = **21 findings**.

---

## Projeto 2 — `ecommerce-api-legacy` (Node.js / Express 4)

**Domínio:** LMS / Checkout (users, courses, enrollments, payments, audit_logs).
**Estrutura atual:** monolítica, 3 arquivos em `src/`.
**Arquivos:** `app.js` (14), `AppManager.js` (141), `utils.js` (25) — ~180 LOC.
**Banco:** SQLite **in-memory** (`:memory:`).

### Achados

| # | Severidade | Categoria | Arquivo:Linha | Descrição |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais hardcoded | `src/utils.js:2-6` | `dbUser`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_..."` no código. |
| 2 | CRITICAL | Vazamento PCI no log | `src/AppManager.js:45` | `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` — número de cartão completo + chave de gateway em log. |
| 3 | CRITICAL | Crypto custom quebrado | `src/utils.js:17-23` | `badCrypto` faz `base64` + slice; reversível, sem salt; não é hash. |
| 4 | CRITICAL | Senha default insegura | `src/AppManager.js:68` | `badCrypto(p \|\| "123456")` — usuário criado sem senha vira "123456". |
| 5 | CRITICAL | "Validação" de cartão por prefixo | `src/AppManager.js:46` | `cc.startsWith("4") ? "PAID" : "DENIED"` no lugar de integração real com gateway. |
| 6 | HIGH | God Class `AppManager` | `src/AppManager.js:1-141` | DB schema + seed + roteamento + lógica de checkout + pagamento + auditoria num único arquivo/classe. |
| 7 | HIGH | Estado global mutável | `src/utils.js:9-10,25` | `globalCache` e `totalRevenue` exportados como singletons mutáveis. |
| 8 | HIGH | Callback hell + sem transação | `src/AppManager.js:28-78` | Checkout faz INSERT enrollment → INSERT payment → INSERT audit_log encadeados; qualquer erro no meio deixa banco inconsistente (sem `BEGIN TRANSACTION`). |
| 9 | HIGH | DELETE deixa órfãos | `src/AppManager.js:131-137` | Comentário no próprio código: "matrículas e pagamentos ficaram sujos no banco." Sem `ON DELETE CASCADE` nem cleanup explícito. |
| 10 | HIGH | DB em memória "em prod" | `src/AppManager.js:7` | `new sqlite3.Database(':memory:')` — dados perdidos em todo restart. |
| 11 | HIGH | Pagamento sem service | `src/AppManager.js:43-64` | Lógica de pagamento dentro do handler de rota, sem porta/adapter. |
| 12 | MEDIUM | N+1 catastrófico | `src/AppManager.js:80-129` | Financial report: para cada course → busca enrollments → para cada enrollment busca user e payment. O(C·E·2). |
| 13 | MEDIUM | API deprecated | `package.json:11` (`express ^4.18.2`), uso de `sqlite3` callback-style | Express 5 é estável; biblioteca moderna seria `better-sqlite3` (sync, sem callbacks). |
| 14 | MEDIUM | Sem middleware de erro | `src/AppManager.js:*` | Cada handler trata erro inline com `res.status(500).send(...)`; sem `error-handler` central. |
| 15 | MEDIUM | Sem rate-limit/helmet/body-limit | `src/app.js:1-14` | Stack só tem `express.json()`; sem mitigação de payload, headers de segurança, CORS controlado. |
| 16 | MEDIUM | Validação superficial | `src/AppManager.js:35` | `if (!u \|\| !e \|\| !cid \|\| !cc)` é todo o input validation; formato de email, Luhn de cartão, formato de senha → nada. |
| 17 | LOW | Nomes ruins | `src/AppManager.js:29-33` | `u`, `e`, `p`, `cid`, `cc` para `name/email/password/courseId/card`. |
| 18 | LOW | `let` desnecessário | `src/AppManager.js:29-33,43,46,...` | Usa `let` para valores que nunca reatribui. |
| 19 | LOW | Idioma misturado | `src/app.js:13` ("Frankenstein LMS rodando"), `src/AppManager.js:35` ("Bad Request"), `:38` ("Curso não encontrado") | PT-BR + inglês alternados. |
| 20 | LOW | Magic strings | `'PAID'`, `'DENIED'` espalhados | Sem enum/const. |
| 21 | LOW | Export morto | `src/utils.js:25` | `totalRevenue` exportado mas nunca usado. |

**Resumo:** 5 CRITICAL · 6 HIGH · 5 MEDIUM · 5 LOW = **21 findings**.

---

## Projeto 3 — `task-manager-api` (Python / Flask 3.0 + SQLAlchemy 3.1)

**Domínio:** Task Manager (users, categories, tasks, com login e relatórios).
**Estrutura atual:** parcialmente organizada — já tem `models/`, `routes/` (blueprints), `services/`, `utils/`. Mas a separação é cosmética: lógica de negócio mora nas rotas.
**Arquivos:** 12 fontes Python (~1000 LOC). Notável: `routes/task_routes.py` (299), `routes/report_routes.py` (223), `routes/user_routes.py` (211).
**Banco:** SQLite via SQLAlchemy (`tasks.db`).

### Achados

| # | Severidade | Categoria | Arquivo:Linha | Descrição |
|---|---|---|---|---|
| 1 | CRITICAL | Hardcoded Secret | `app.py:13` | `SECRET_KEY = 'super-secret-key-123'`. |
| 2 | CRITICAL | Hash de senha quebrado | `models/user.py:29,32` | `hashlib.md5(pwd.encode()).hexdigest()` sem salt; MD5 é considerado quebrado desde 2004. |
| 3 | CRITICAL | Credenciais SMTP hardcoded | `services/notification_service.py:8-11` | `taskmanager@gmail.com / senha123` no código. |
| 4 | CRITICAL | Senha exposta na API | `models/user.py:17-25` | `to_dict()` inclui `'password': self.password` — é o hash MD5, mas ainda assim vaza. |
| 5 | CRITICAL | "JWT" falso | `routes/user_routes.py:210` | `'token': 'fake-jwt-token-' + str(user.id)` — qualquer um forja. |
| 6 | HIGH | Fat Controllers | `routes/task_routes.py:12-63`, `routes/report_routes.py:13-101`, `routes/user_routes.py:42-90` | Agregações, formatação, regras de overdue/completion_rate vivem nas rotas. |
| 7 | HIGH | `except:` catch-all | `routes/task_routes.py:62,137,204,236`, `routes/user_routes.py:130,150`, `routes/report_routes.py:186,208,222` | Bare `except:` engole `KeyboardInterrupt` e `SystemExit` também; mascara bugs. |
| 8 | HIGH | Lógica duplicada (DRY) | `models/task.py:50-60` ↔ `routes/task_routes.py:30-39,71-80` ↔ `routes/user_routes.py:171-180` ↔ `routes/report_routes.py:34-43` | Cálculo de `is_overdue` reimplementado 4×. |
| 9 | HIGH | Blueprint com domínio errado | `routes/report_routes.py:157-223` | CRUD de **categorias** mora dentro de `report_routes`. |
| 10 | HIGH | Service sem injeção | `services/notification_service.py:1-48` | `NotificationService` nunca é instanciado/usado por nenhuma rota; sem DI; credenciais no `__init__`. |
| 11 | MEDIUM | N+1 query | `routes/task_routes.py:41-58` | Para cada task, chama `User.query.get` e `Category.query.get`. |
| 12 | MEDIUM | N+1 em relatório | `routes/report_routes.py:54-68` | Para cada user, query separada de tasks. |
| 13 | MEDIUM | Validação ad-hoc | `routes/task_routes.py:86-145`, `routes/user_routes.py:46-78` | Sem `marshmallow`/`pydantic` apesar de estar em `requirements.txt`. |
| 14 | MEDIUM | Imports não usados | `routes/task_routes.py:7` (`os, sys, time, json`), `routes/user_routes.py:6` (`hashlib, json`), `utils/helpers.py:4-7` (`os, sys, math`) | Sinal de copy-paste e ferramentas de lint ausentes. |
| 15 | MEDIUM | `db.create_all()` no boot | `app.py:30-31` | Sem migrations (Alembic) — schema diverge silenciosamente entre ambientes. |
| 16 | LOW | API deprecated | `models/task.py:15,16`, `routes/task_routes.py:31,72,285`, `routes/user_routes.py:172`, `routes/report_routes.py:35,45-46` | `datetime.utcnow()` está deprecated desde Python 3.12 → use `datetime.now(timezone.utc)`. |
| 17 | LOW | API deprecated (SQLAlchemy) | `routes/task_routes.py:67,117,123,158,189,195,228`, `routes/user_routes.py:29,94,117,196`, `routes/report_routes.py:106,159,162,191,213` | `Model.query.get(id)` é legacy desde SQLAlchemy 2.0 → use `db.session.get(Model, id)`. |
| 18 | LOW | `type(x) == list` | `routes/task_routes.py:141,210`, `utils/helpers.py:103` | Não-pythonic; quebra com subclasses. Use `isinstance`. |
| 19 | LOW | Magic numbers | `models/task.py:46-47` (priority 1-5), `utils/helpers.py:114-115` (`MIN_PASSWORD_LENGTH = 4`, `MAX_TITLE_LENGTH = 200`) | Sem enum/config central; `MIN_PASSWORD_LENGTH = 4` é absurdamente baixo. |
| 20 | LOW | Status strings espalhadas | `'pending'/'in_progress'/'done'/'cancelled'` em 7+ lugares | Sem `enum.Enum`. |
| 21 | LOW | `print` como logging | `routes/task_routes.py:149,153,219,235`, `routes/user_routes.py:83,89,147` | Sem `logging`. |

**Resumo:** 5 CRITICAL · 5 HIGH · 5 MEDIUM · 6 LOW = **21 findings**.

---

## Padrões transversais (servem para o catálogo da skill)

A skill precisa detectar de forma agnóstica a stack:

1. **Hardcoded secrets** — regex de chaves/senhas no código fonte.
2. **SQL Injection** — concatenação `+ str(...)` ou template-string em `execute/run/all`.
3. **Plaintext / weak crypto password** — coluna `senha/password TEXT`; `md5`, `sha1`, base64, ROT13.
4. **Sensitive data leak** — `password/senha/secret_key/card` aparecendo em `jsonify`/`res.json` ou em `print/console.log`.
5. **God Class / God Module** — arquivo único > ~250 linhas misturando DB + roteamento + regra.
6. **Mutable global state** — variáveis de módulo reatribuíveis (cache, conexão, contador).
7. **Fat Controller** — handler de rota com loops/agregação/regras de negócio acima de ~30 linhas.
8. **Missing transaction** — múltiplos inserts/updates sem `BEGIN/COMMIT` ou ORM `session.begin()`.
9. **N+1 query** — `for ... in result: db.query(...)` aninhado.
10. **Bare except / engolir erro** — `except:`, `catch (_) {}`, retornos genéricos sem log.
11. **APIs deprecated** — `datetime.utcnow`, `Query.get`, `sqlite3.verbose` callback-style, Flask `before_first_request`, Express ≤4.
12. **CORS aberto / debug em prod** — `CORS(app)` sem `origins`; `DEBUG=True`; `app.run(debug=True)`.
13. **Validação ausente / duplicada** — regex de email faltando; mesmo bloco de `if not data...` repetido em create/update.
14. **Naming / magic numbers** — vars de uma letra; literais numéricos repetidos sem constante.
15. **Logging com `print` / `console.log`** — em vez de `logging` / `winston`.

---

## Mapa de transformação para MVC alvo

Estrutura que a Fase 3 deve produzir, com adaptações por stack:

### Python/Flask
```
src/
├── app.py                    # composition root
├── config/
│   └── settings.py           # SECRET_KEY/DEBUG via env
├── models/                   # ORM ou DAO por domínio
│   ├── produto.py
│   └── usuario.py
├── controllers/              # orquestra request → service → response
│   ├── produto_controller.py
│   └── usuario_controller.py
├── services/                 # regra de negócio (opcional, recomendado)
│   ├── pedido_service.py
│   └── notification_service.py
├── views/
│   └── routes.py             # blueprints/rotas
├── middlewares/
│   └── error_handler.py
└── utils/
    └── validators.py
```

### Node.js/Express
```
src/
├── app.js                    # composition root
├── server.js                 # http listen separado do app
├── config/
│   └── index.js
├── models/
│   └── *.js                  # acesso a dados por entidade
├── controllers/
│   └── *.controller.js
├── services/
│   └── *.service.js
├── routes/
│   └── *.routes.js
├── middlewares/
│   ├── error.js
│   └── validate.js
└── utils/
```

### Critérios "MVC OK" para a Fase 3
- Nenhum `SECRET_KEY` hardcoded; tudo via `os.environ` / `process.env`.
- Nenhuma query SQL concatenada com input do usuário.
- Senhas com `bcrypt`/`argon2` (Python) ou `bcrypt`/`scrypt` (Node).
- Nenhum endpoint expondo `password/secret/api_key` no JSON.
- Cada controller tem ≤ 1 responsabilidade (CRUD de 1 entidade).
- Error handler centralizado registrado uma vez.
- `app.py`/`app.js` é só composição: importa, monta, expõe.
- Boot da aplicação verificado com `python app.py` / `npm start`.
- Endpoints originais respondem (smoke test com curl no health + 1 GET de cada blueprint).

---

## Cobertura mínima para o desafio

O enunciado pede, por projeto, **≥5 problemas** (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW). Os três projetos têm **21 findings cada** — folga grande para a skill detectar 5+ em qualquer execução.
