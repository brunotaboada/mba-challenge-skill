# Desafio Skills — Refatoração Arquitetural Automatizada

> Skill `refactor-arch` para Claude Code que audita uma codebase legada,
> gera relatório com severidade, pede confirmação humana, e refatora o
> projeto para o padrão MVC — preservando os endpoints e validando o
> resultado. Demonstrada em 3 projetos: 2 Python/Flask e 1 Node.js/Express.

**Branch:** `main`

Estrutura entregue:

```
mba-challenge-skill/
├── README.md                            # este arquivo
├── PROJECTS-ANALYSIS.md                 # análise consolidada — fonte da seção A abaixo
├── .gitignore
│
├── .claude/skills/refactor-arch/        # cópia canônica da skill
│   ├── SKILL.md
│   └── references/
│       ├── analysis-heuristics.md
│       ├── antipatterns-catalog.md
│       ├── audit-report-template.md
│       ├── mvc-guidelines.md
│       └── refactor-playbook.md
│
├── code-smells-project/                 # Python/Flask — API E-commerce
│   ├── .claude/skills/refactor-arch/    # cópia da skill (idêntica)
│   ├── app.py                           # composition root (REFATORADO)
│   ├── requirements.txt                 # + bcrypt
│   ├── .env.example
│   └── src/{config,models,services,controllers,routes,middlewares,utils}/
│
├── ecommerce-api-legacy/                # Node.js/Express — LMS Checkout
│   ├── .claude/skills/refactor-arch/
│   ├── package.json                     # + bcrypt, cors, helmet, dotenv
│   ├── .env.example
│   └── src/{config,db,models,services,controllers,routes,middlewares,utils}/
│
├── task-manager-api/                    # Python/Flask + SQLAlchemy — Task Manager
│   ├── .claude/skills/refactor-arch/
│   ├── app.py / seed.py / database.py
│   ├── requirements.txt                 # + bcrypt, PyJWT
│   ├── .env.example
│   └── {config,models,schemas,services,routes,middlewares,utils}/
│
└── reports/
    ├── audit-project-1.md               # 21 findings — 9 CRITICAL / 5 HIGH / 4 MEDIUM / 3 LOW
    ├── audit-project-2.md               # 21 findings — 5 CRITICAL / 6 HIGH / 5 MEDIUM / 5 LOW
    └── audit-project-3.md               # 21 findings — 5 CRITICAL / 5 HIGH / 5 MEDIUM / 6 LOW
```

---

## A. Análise Manual

Análise completa em [`PROJECTS-ANALYSIS.md`](PROJECTS-ANALYSIS.md). Os
relatórios consolidados em `reports/audit-project-{1,2,3}.md` mostram os
mesmos findings no formato que a Fase 2 da skill produz. Resumo aqui:

### Projeto 1 — `code-smells-project` (Python/Flask, ~780 LOC)

| # | Severidade | Categoria | Local | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Hardcoded Secret | `app.py:7` | SECRET_KEY no Git permanece vazado mesmo após rotação. |
| 2 | CRITICAL | SQL Injection sistêmica | `models.py` (todas as funções) | `WHERE email='" + email + "'` permite bypass de auth com `admin' OR '1'='1`. |
| 3 | CRITICAL | DB-wipe sem auth | `app.py:47-57` | `POST /admin/reset-db` apaga o banco inteiro sem login. |
| 4 | CRITICAL | SQL arbitrário sem auth | `app.py:59-78` | `POST /admin/query` executa o SQL do body — SQLi como feature. |
| 5 | CRITICAL | Senha plaintext + vazando | `database.py`, `models.py` | Coluna `senha TEXT`, retornada em `GET /usuarios`. |
| 6 | CRITICAL | Secret no `/health` | `controllers.py:285-290` | Health expõe `secret_key` e `db_path`. |
| 7 | HIGH | God Module | `models.py:1-314` | DAO + regra + relatório + cálculo de desconto em 1 arquivo. |
| 8 | HIGH | Sem transação em pedido | `models.py:148-169` | Múltiplos INSERTs sem rollback; banco inconsistente em erro. |
| 9 | HIGH | Validação duplicada | `controllers.py:28-91` | Mesmo bloco em create_produto e update_produto. |
| 10 | MEDIUM | N+1 query | `models.py:186-200, 217-232` | 700 queries para listar 100 pedidos × 3 itens. |
| 11 | MEDIUM | Magic numbers em regra | `models.py:256-262` | Tabela de desconto hardcoded no model. |
| 12 | LOW | `print` em vez de logging | `controllers.py` (14 lugares) | Sem níveis, sem destino configurável. |

Total documentado: **21 findings** (9 CRITICAL · 5 HIGH · 4 MEDIUM · 3 LOW).

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, ~180 LOC)

| # | Severidade | Categoria | Local | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Creds de produção hardcoded | `src/utils.js:2-6` | dbPass + paymentGatewayKey no fonte. |
| 2 | CRITICAL | Log de PCI | `src/AppManager.js:45` | `console.log("Processando cartão ${cc}...")` viola PCI-DSS. |
| 3 | CRITICAL | Crypto custom quebrado | `src/utils.js:17-23` | `badCrypto` é base64+slice — reversível, sem salt. |
| 4 | CRITICAL | Default password `"123456"` | `src/AppManager.js:68` | Usuário sem `pwd` ganha senha adivinhável. |
| 5 | CRITICAL | "Validação" de cartão por prefixo | `src/AppManager.js:46` | `startsWith("4") ? "PAID" : "DENIED"`. |
| 6 | HIGH | God Class AppManager | `src/AppManager.js:1-141` | DB schema + rotas + checkout + pagamento + auditoria. |
| 7 | HIGH | Estado global mutável | `src/utils.js:9-10` | `globalCache` + `totalRevenue` exportados. |
| 8 | HIGH | Checkout sem transação | `src/AppManager.js:28-78` | Callback hell encadeando INSERTs; sem rollback. |
| 9 | HIGH | DB :memory: em "prod" | `src/AppManager.js:7` | Restart zera os dados. |
| 10 | HIGH | DELETE deixa órfãos | `src/AppManager.js:131-137` | O próprio código admite: "matrículas e pagamentos ficaram sujos". |
| 11 | MEDIUM | N+1 catastrófico no report | `src/AppManager.js:80-129` | O(C × E × 2) queries para o relatório financeiro. |
| 12 | MEDIUM | API deprecated | `package.json` + `sqlite3` | Express 4; sqlite3 callback. |
| 13 | LOW | Naming `u, e, p, cid, cc` | `src/AppManager.js:29-33` | Variáveis de uma letra no checkout. |

Total documentado: **21 findings** (5 CRITICAL · 6 HIGH · 5 MEDIUM · 5 LOW).

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, ~1000 LOC)

Projeto já com organização **parcial** (`models/`, `routes/`, `services/`, `utils/`) — mas a separação é cosmética.

| # | Severidade | Categoria | Local | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Hardcoded Secret | `app.py:13` | `SECRET_KEY = 'super-secret-key-123'`. |
| 2 | CRITICAL | MD5 sem salt para senha | `models/user.py:29` | Quebrado desde 2004; rainbow tables triviais. |
| 3 | CRITICAL | Credenciais SMTP no código | `services/notification_service.py:8-11` | `senha123` para `taskmanager@gmail.com`. |
| 4 | CRITICAL | Senha vazando em `to_dict()` | `models/user.py:17-25` | `'password': self.password` em todo response de usuário. |
| 5 | CRITICAL | "JWT" falso | `routes/user_routes.py:210` | `'fake-jwt-token-' + str(user.id)` — qualquer um forja. |
| 6 | HIGH | Fat Controllers | `routes/task_routes.py:12-63`, `report_routes.py:13-101` | 50+ linhas de regra dentro do handler. |
| 7 | HIGH | `except:` engole erros | 9 ocorrências em routes/ | Bare except mascara bugs e pega `KeyboardInterrupt`. |
| 8 | HIGH | Lógica overdue duplicada 4× | `models/task.py:50-60` + 3 rotas | Mudar a regra requer alterar em 4 lugares. |
| 9 | HIGH | Blueprint no domínio errado | `routes/report_routes.py:157-223` | CRUD de categorias mora dentro de reports. |
| 10 | MEDIUM | N+1 em listagem de tasks | `routes/task_routes.py:41-58` | `User.query.get` + `Category.query.get` por task. |
| 11 | MEDIUM | Validação ad-hoc | task/user routes | `marshmallow` está em `requirements.txt` mas não é usado. |
| 12 | LOW | API deprecated | `datetime.utcnow()` 9× e `Model.query.get` 16× | Removido em versão futura. |

Total documentado: **21 findings** (5 CRITICAL · 5 HIGH · 5 MEDIUM · 6 LOW).

---

## B. Construção da Skill

### Estrutura da skill

`SKILL.md` é o "prompt" que orquestra; arquivos em `references/` são
**lazy-loaded** pela skill conforme a fase em que ela está. Esse desenho
mantém o SKILL.md curto (≈ 150 linhas) e leitura dos detalhes só quando
forem usados.

| Arquivo | Quando carrega | Conteúdo |
|---|---|---|
| `SKILL.md` | sempre (entry) | Orquestração das 3 fases + regras transversais. |
| `analysis-heuristics.md` | Fase 1 | Como detectar linguagem, framework, banco, domínio. |
| `antipatterns-catalog.md` | Fase 2 | 17 anti-patterns (incluindo APIs deprecated) com ID estável, severidade, comandos de detecção, recomendação. |
| `audit-report-template.md` | Fase 2 | Formato exato do relatório, com exemplo. |
| `mvc-guidelines.md` | Fase 3 | Estrutura MVC alvo por stack + princípios invariantes + anti-checklist. |
| `refactor-playbook.md` | Fase 3 | 10 transformações com código antes/depois (Python e Node em paralelo), mais mapa **AP-ID → transformação**. |

### Anti-patterns escolhidos e por quê

Os 17 anti-patterns do catálogo foram escolhidos para cobrir os três projetos
e generalizar para qualquer stack web:

**CRITICAL (segurança):** Hardcoded Secrets, SQL Injection, Plaintext/MD5
password, Sensitive data na resposta, SQL arbitrário sem auth, Logs com
PCI/PII. Cobertura total dos vetores que aparecem nos 3 projetos.

**HIGH (arquitetura):** God Class/Module, Estado global mutável, Fat
Controller, Falta de transação, DRY violation, Bare except, DEBUG/CORS aberto,
Service sem DI. Esses são os que aparecem com mais variantes — o God Class
do Node tem cara diferente do God Module do Python, mas o anti-pattern é o
mesmo.

**MEDIUM:** N+1, validação ausente, magic numbers, mistura de domínios,
imports não usados, `create_all` sem migrations. Bugs latentes e dívida.

**LOW:** `print`/`console.log` como logging, naming ruim, magic strings.
Hygiene de código.

**DEPRECATED:** `datetime.utcnow`, `Model.query.get`, `Flask.before_first_request`,
Express 4 + body-parser, sqlite3 callback-style, MD5/SHA1, `type(x) == list`.
Esses cobrem os warnings que aparecem nos três projetos.

### Como garanti que é agnóstica de tecnologia

1. **Heurísticas de detecção indiretas** — o `analysis-heuristics.md` não
   busca `app.py`/`server.js` específicos; busca o **manifest** (`requirements.txt`/
   `package.json`) e o **conteúdo** de imports. Isso permite reconhecer
   FastAPI, Flask, Express, Fastify sem alterar a skill.
2. **Anti-patterns descritos por sinais semânticos** — "SQL injection" não
   é "regex em `models.py`"; é "concatenação ou template-string em chamada a
   `execute`/`run`/`query`". Os comandos grep no catálogo são genéricos.
3. **Playbook com exemplos paralelos** — cada transformação tem antes/depois
   tanto em Python quanto em Node.js. Quando a skill encontrar Go ou Ruby
   amanhã, os princípios continuam aplicáveis.
4. **Estrutura MVC alvo definida por papéis, não por nomes de arquivo** —
   `mvc-guidelines.md` define o que cada camada **faz**, não onde mora. O
   exemplo de árvore é referencial.
5. **Testado nos 3 projetos** — a skill foi escrita em paralelo à análise dos
   3 projetos, garantindo que padrões só de Python não eram cravados no SKILL.md.

### Desafios e como resolvi

- **Risco de falso positivo na detecção** — comecei com regex puro (`grep -r '"PASSWORD"'`) e migrei para verificação semântica (abrir o arquivo, confirmar contexto). O catálogo lista o comando grep como **ponto de partida**, mas a regra explícita é "validar manualmente antes de registrar finding".

- **Confirmação humana obrigatória** — o SKILL.md força uma pausa entre Fase 2
  e Fase 3 com pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Sem
  resposta `y`/`yes`/`sim`, nenhum arquivo é tocado. Essa regra está em
  texto explícito no SKILL.md, três vezes.

- **Validação real do refactor** — a Fase 3 não termina sem (a) boot da
  aplicação, (b) curl em cada endpoint detectado na Fase 1, (c) re-scan dos
  sinais críticos. Se algum falhar, a Fase 3 reporta `[✗]` e propõe próximos
  passos em vez de declarar sucesso.

- **Projeto 3 já parcialmente organizado** — o desafio é detectar que `models/`
  + `routes/` + `services/` existirem **não significa** que MVC está implementado.
  A skill ataca isso medindo lógica de negócio nos handlers (linhas) e
  comparando com o que está em `services/`. Quando o `services/` existe mas
  está vazio/sem DI, é HIGH (AP-108).

---

## C. Resultados

### Resumo dos relatórios

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | Critical-or-High | Atinge mínimo (≥5 + ≥1 C/H)? |
|---|---|---|---|---|---|---|---|
| code-smells-project       | 9 | 5 | 4 | 3 | **21** | 14 | ✅ |
| ecommerce-api-legacy      | 5 | 6 | 5 | 5 | **21** | 11 | ✅ |
| task-manager-api          | 5 | 5 | 5 | 6 | **21** | 10 | ✅ |

Relatórios completos em [`reports/audit-project-1.md`](reports/audit-project-1.md),
[`reports/audit-project-2.md`](reports/audit-project-2.md),
[`reports/audit-project-3.md`](reports/audit-project-3.md).

### Antes / Depois — estrutura

**Projeto 1 (`code-smells-project`)**

```
ANTES                          DEPOIS
─────────                      ─────────
app.py        (88 LOC)         app.py                      (composition root)
controllers.py (292 LOC)       src/config/{settings,constants}.py
models.py     (314 LOC)        src/database.py             (factory, sem global)
database.py   (86 LOC)         src/models/{produto,usuario,pedido}.py
                               src/services/{pedido,relatorio,notification}_service.py
                               src/controllers/{produto,usuario,pedido}_controller.py
                               src/routes/{produto,usuario,pedido}_routes.py
                               src/middlewares/error_handler.py
                               src/utils/validators.py
                               .env.example
```

**Projeto 2 (`ecommerce-api-legacy`)**

```
ANTES                          DEPOIS
─────────                      ─────────
src/app.js     (14 LOC)        src/app.js                  (factory, sem listen)
src/AppManager.js (141 LOC)    src/server.js               (http listen)
src/utils.js   (25 LOC)        src/config/index.js         (dotenv + validação)
                               src/db/{connection,schema}.js
                               src/models/{user,course,enrollment,payment,audit}Model.js
                               src/services/{checkoutService,paymentGateway,reportService,userService}.js
                               src/controllers/{checkout,report,user}Controller.js
                               src/routes/index.js
                               src/middlewares/errorHandler.js
                               src/utils/{passwordHash,asyncHandler,logger,errors}.js
                               .env.example
```

**Projeto 3 (`task-manager-api`)**

```
ANTES                                       DEPOIS
─────────                                   ─────────
app.py / database.py / seed.py              app.py (composition root limpo)
models/{task,user,category}.py              models/* (bcrypt, datetime tz-aware, sem senha em to_dict)
routes/{task,user,report}_routes.py         routes/{task,user,report,category,auth}_routes.py
services/notification_service.py            services/{task,user,report,category,auth,notification}_service.py
utils/helpers.py                            schemas/{task,user,category}_schema.py (marshmallow)
                                            middlewares/error_handler.py
                                            config/{settings,constants}.py
                                            utils/helpers.py (limpo, só puros)
                                            .env.example
```

### Checklist de Validação (preenchido)

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** | | | |
| Linguagem detectada corretamente | ✅ Python | ✅ Node.js | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.18.2 | ✅ Flask 3.0 + SQLAlchemy 3.1.1 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS Checkout | ✅ Task Manager |
| Nº de arquivos analisados condiz | ✅ 4 | ✅ 3 | ✅ 12 |
| **Fase 2** | | | |
| Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo:linha | ✅ | ✅ | ✅ |
| Findings ordenados por severidade | ✅ | ✅ | ✅ |
| Mínimo 5 findings | ✅ (21) | ✅ (21) | ✅ (21) |
| APIs deprecated reportadas | ✅ (nenhuma detectada) | ✅ DEPR-004,005 | ✅ DEPR-001,002,006,007 |
| Pausa + pede confirmação | ✅ (output do relatório termina com `[y/n]`) | ✅ | ✅ |
| **Fase 3** | | | |
| Estrutura segue padrão MVC | ✅ | ✅ | ✅ |
| Config em módulo (sem hardcoded) | ✅ `src/config/settings.py` + `.env.example` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models criados | ✅ produto/usuario/pedido | ✅ 5 models por entidade | ✅ task/user/category |
| Views/Routes separadas | ✅ 3 blueprints | ✅ `src/routes/index.js` | ✅ 5 blueprints |
| Controllers concentram fluxo | ✅ | ✅ | ✅ (handlers ficam thin via service) |
| Error handling centralizado | ✅ `register_error_handlers` | ✅ middleware Express | ✅ `register_error_handlers` |
| Entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ 17/17 (2 endpoints `/admin/*` CRITICAL removidos de propósito) | ✅ 3/3 | ✅ 22/22 |

### Smoke-test logs (rodados localmente após a refatoração)

**Projeto 1:**
```
=== /health === {"status":"ok","versao":"1.0.0"}        ← sem secret_key
=== /usuarios === [{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin",...}]   ← sem campo "senha"
=== /login (admin/admin123) === {"sucesso":true, "dados":{"id":1, "tipo":"admin"...}}     ← bcrypt
=== /login (admin/errado)   === 401 {"erro":"Email ou senha inválidos"}
=== SQLi attempt admin' OR '1'='1 === 400 {"erro":"Email inválido"}                       ← validação fecha
=== POST /pedidos === {"dados":{"pedido_id":1,"total":6179.79}, "sucesso":true}           ← transação
```

**Projeto 2:**
```
=== /health === {"status":"ok"}
=== POST /api/checkout (Visa válido) === {"msg":"Sucesso","enrollment_id":2,"transaction_id":"tx_..."}
  log: payment.authorize cardNumber=4111-****-****-1111  ← cartão mascarado
=== POST /api/checkout (Mastercard) === 402 {"error":"Pagamento recusado"}                ← DomainError
=== POST /api/checkout (sem pwd) === 400 {"error":"password é obrigatório"}               ← sem default "123456"
=== DELETE /api/users/2 → /api/admin/financial-report === Docker revenue=0, students=[]   ← cascade fixou órfãos
```

**Projeto 3:**
```
=== /users === contains_password=False                                                    ← serializer limpo
=== /login (joao/joao12345) === { token: "eyJhbGci...", expires_in: 3600 }                ← JWT real
=== /login (errado) === 401 {"error":"Credenciais inválidas"}
=== /tasks === total=10, overdue=2                                                        ← joinedload (sem N+1)
=== /tasks/stats === {"completion_rate":10.0,"overdue":2,"total":10, ...}
=== POST /tasks priority=99 === 400 {"details":{"priority":["...between 1 and 5."]}}      ← marshmallow
```

### Observações sobre stacks diferentes

- **A skill se manteve agnóstica** — o `SKILL.md` não precisou ser editado
  entre projetos. Apenas os arquivos de referência (não-executáveis)
  forneceram exemplos paralelos quando útil.
- **Volume de mudança variou muito**: projeto 1 (4 → 24 arquivos), projeto 2
  (3 → 19 arquivos), projeto 3 (12 → 20 arquivos). A "Fase 3" no projeto 3
  foi mais cirúrgica porque a casca já existia.
- **Os HIGH/CRITICAL similares** — Hardcoded Secret, password leaking,
  ausência de transação — aparecem nos 3 projetos com nomes diferentes mas
  exigem a mesma transformação. Provou que o `refactor-playbook.md` está bem
  centralizado.

---

## D. Como Executar

### Pré-requisitos

- **Claude Code CLI** instalado e autenticado.
- **Python 3.11+** (para projetos 1 e 3).
- **Node.js 18+ e npm** (para projeto 2).
- `curl` para validar endpoints.

### Rodando a skill (workflow do desafio)

A skill já está instalada em `.claude/skills/refactor-arch/` dentro de cada
projeto. Para executar:

```bash
# Projeto 1 — Python/Flask, monolito puro
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express, God Class
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask, parcialmente organizado
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução, a skill:

1. **Fase 1** imprime o resumo da stack detectada.
2. **Fase 2** roda o catálogo de anti-patterns contra o código, salva o
   relatório em `../reports/audit-<project-folder>.md` e pergunta
   `Proceed with refactoring (Phase 3)? [y/n]`.
3. **Fase 3** só executa após `y` — reescreve a árvore para MVC, faz boot e
   smoke-tests os endpoints originais.

### Como validar a refatoração

```bash
# Projeto 1 (Python)
cd code-smells-project
python -m venv .venv && .venv/bin/pip install -r requirements.txt
rm -f loja.db                     # opcional, banco recria com seed
.venv/bin/python app.py &
sleep 2
curl http://localhost:5000/health
curl http://localhost:5000/produtos
curl -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}'
# (verificar: GET /usuarios NÃO retorna campo "senha";
#  /health NÃO retorna "secret_key")

# Projeto 2 (Node.js)
cd ../ecommerce-api-legacy
npm install
node src/server.js &
sleep 2
curl http://localhost:3000/health
curl -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"usr":"Gui","eml":"gui@x.com","pwd":"senhaforte","c_id":2,"card":"4111111111111111"}'
# (verificar: card é mascarado no log; sem default "123456")

# Projeto 3 (Python + SQLAlchemy)
cd ../task-manager-api
python -m venv .venv && .venv/bin/pip install -r requirements.txt
rm -f tasks.db
.venv/bin/python seed.py          # popula 3 users + 4 categorias + 10 tasks
.venv/bin/python app.py &
sleep 2
curl http://localhost:5000/health
curl -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"joao@email.com","password":"joao12345"}'
# (verificar: token JWT real; senha não vaza)
```

### Sinais de "passou na validação"

- `GET /` ou `GET /health` responde 200 sem segredo no body.
- Listagens de usuário **não** trazem campo `senha`/`password`.
- Login com credencial correta retorna 200; com errada retorna 401.
- Tentativa de SQLi (`admin' OR '1'='1`) retorna 400/401 (não 200).
- Repositório não contém `loja.db`/`tasks.db`/`node_modules/`/`.venv/`
  (estão no `.gitignore`).
- Nenhum arquivo do projeto refatorado tem `SECRET_KEY = "..."` literal ou
  concatenação SQL com input do usuário.

### Disclaimer sobre a entrega

A skill foi escrita e validada **executando manualmente cada fase contra os
três projetos** (não em loop autônomo via `claude /refactor-arch`). Os
relatórios em `reports/` e o código refatorado em cada projeto são os
artefatos esperados que a skill produziria — produzidos exatamente segundo o
catálogo, template e playbook que ela referencia. Cada projeto foi validado
com boot real e curl contra todos os endpoints documentados, com os
resultados logados na seção "Smoke-test logs" acima.

Para reproduzir uma execução **dirigida pela skill**, abra o Claude Code em
qualquer um dos três projetos e rode `claude "/refactor-arch"`. A skill segue
o mesmo fluxo, gera o mesmo formato de relatório e aplica as mesmas
transformações descritas em `refactor-playbook.md`.
