================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-05-14

## Phase 1 — Project Analysis

```
Language:      Node.js
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API com fluxo de checkout (users, courses, enrollments, payments)
Architecture:  God Class — AppManager.js concentra DB + rotas + checkout + pagamento + auditoria
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs
```

Endpoints detectados:
- `POST   /api/checkout`
- `GET    /api/admin/financial-report`
- `DELETE /api/users/:id`

## Summary

| Severidade | Quantidade |
|---|---|
| CRITICAL | 5 |
| HIGH     | 6 |
| MEDIUM   | 5 |
| LOW      | 5 |
| **Total**| **21** |

Critical-or-High count: 11 (≥1 required by acceptance criteria) ✓

## Findings

### [CRITICAL] Credenciais de produção hardcoded  (AP-001)
File: `src/utils.js:2-6`
Description: Bloco `config` exporta `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser` — todos como literais.
Impact: Push para qualquer repo público (e o histórico do Git já carrega) compromete banco + gateway de pagamento + email.
Recommendation: T-001 — mover para `process.env`, validar presença com fail-fast, fornecer `.env.example`.

### [CRITICAL] Log de PCI — número de cartão e gateway key  (AP-006)
File: `src/AppManager.js:45`
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` durante o checkout.
Impact: Violação direta de PCI-DSS (cartão completo em log). Em ambiente com agregador de logs (ELK, CloudWatch) o dado fica retido indefinidamente.
Recommendation: T-010 — mascarar (`****-****-****-1234`) ou nunca logar; usar `pino` com redactors em campos sensíveis.

### [CRITICAL] Crypto customizado quebrado para senha  (AP-003)
File: `src/utils.js:17-23`
Description: `badCrypto(pwd)` faz `Buffer.from(pwd).toString('base64').substring(0,2)` 10000 vezes e devolve os primeiros 10 chars. Não é hash criptográfico: é reversível, sem salt, com colisão trivial.
Impact: Senhas armazenadas são facilmente revertidas/colididas; brute-force imediato.
Recommendation: T-003 — substituir por `bcrypt.hash(pwd, 10)` + `bcrypt.compare(...)`.

### [CRITICAL] Senha padrão "123456"  (AP-001)
File: `src/AppManager.js:68`
Description: No checkout, se o body não traz `pwd`, o código usa `"123456"`: `badCrypto(p || "123456")`.
Impact: Usuários criados sem senha ficam com `"123456"` como credencial — adivinhável.
Recommendation: Falhar a requisição se `pwd` estiver ausente; nunca chutar default.

### [CRITICAL] "Validação" de cartão por prefixo  (AP-202)
File: `src/AppManager.js:46`
Description: `cc.startsWith("4") ? "PAID" : "DENIED"` — toda lógica de "processamento de pagamento".
Impact: Qualquer string que comece com `4` aprova compra; não há gateway real, não há autorização, não há captura. Fraude trivial.
Recommendation: Adapter `paymentGateway` real (Stripe/Pagar.me/mock-em-dev); separar em service.

### [HIGH] God Class — AppManager  (AP-101)
File: `src/AppManager.js:1-141`
Description: A classe `AppManager` faz: criação de schema (initDb), seed de dados, registro de rotas (setupRoutes), lógica de checkout, processamento de pagamento, gravação de matrícula, gravação de pagamento, auditoria, cache.
Impact: Impossível trocar uma responsabilidade sem mexer no resto; impossível testar checkout sem subir o app inteiro.
Recommendation: T-005 — separar em `models/`, `services/checkoutService`, `services/paymentGateway`, `controllers/checkoutController`, `routes/checkoutRoutes`.

### [HIGH] Estado global mutável  (AP-102)
File: `src/utils.js:9-10, 25`
Description: `let globalCache = {}` e `let totalRevenue = 0` declarados como singletons mutáveis no módulo. `globalCache` é alimentado por `logAndCache` chamado dentro do checkout. `totalRevenue` é exportado mas nunca usado.
Impact: Estado compartilhado entre requests; race conditions; impossível resetar para teste; memory leak se a chave de cache crescer.
Recommendation: T-005 — encapsular cache em instância request-scoped ou trocar por `node-cache`/Redis; remover `totalRevenue`.

### [HIGH] Callback hell sem transação no checkout  (AP-104)
File: `src/AppManager.js:28-78`
Description: O checkout encadeia: `db.get` (course) → `db.get` (user) → `db.run` (insert user se novo) → `db.run` (insert enrollment) → `db.run` (insert payment) → `db.run` (insert audit_log). Sem `BEGIN TRANSACTION`. Falha em qualquer ponto deixa banco inconsistente.
Impact: Usuário criado sem enrollment; enrollment sem payment; auditoria pulada. Pior cenário em produção.
Recommendation: T-006 — usar `db.serialize` com `BEGIN`/`COMMIT`/`ROLLBACK` explícitos, ou migrar para `better-sqlite3` com `db.transaction(...)`.

### [HIGH] DELETE de usuário deixa órfãos  (AP-104, AP-103)
File: `src/AppManager.js:131-137`
Description: `DELETE /api/users/:id` remove o usuário e o próprio código admite: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`.
Impact: Integridade referencial perdida; relatórios financeiros somam pagamentos sem usuário associado.
Recommendation: Definir `ON DELETE CASCADE` nas FKs ou fazer delete em transação, removendo enrollments e payments associados.

### [HIGH] SQLite in-memory "em produção"  (AP-102)
File: `src/AppManager.js:7`
Description: `new sqlite3.Database(':memory:')` — todos os dados ficam em memória e se perdem a cada restart.
Impact: Reinicializar o servidor zera matrículas e pagamentos. Inviável para produção.
Recommendation: Caminho de arquivo (`process.env.DB_PATH || './data/lms.db'`) ou migrar para banco real (Postgres/MySQL).

### [HIGH] Lógica de pagamento dentro do handler (sem service)  (AP-103, AP-108)
File: `src/AppManager.js:43-64`
Description: A função `processPaymentAndEnroll` está aninhada no handler da rota, capturando `cc`, `cid`, `course` via closure. Não há `paymentGateway` adapter, não há injeção de dependência.
Impact: Impossível mockar gateway para teste; trocar provider exige reescrever a rota.
Recommendation: T-005 — `services/paymentGateway.js` com interface `authorize(card, amount)`; `services/checkoutService.js` orquestra.

### [HIGH] Sem error handler centralizado  (AP-106)
File: `src/AppManager.js` (handlers inteiros)
Description: Cada callback responde 500 inline: `res.status(500).send("Erro DB")`. Sem `app.use((err, req, res, next) => ...)`; mensagens inconsistentes; alguns callbacks engolem erro sem responder.
Impact: Cliente recebe respostas inconsistentes; observabilidade ruim; bug fácil de mascarar.
Recommendation: T-008 — middleware `errorHandler.js` registrado por último; controllers usam `asyncHandler` para deixar erro subir.

### [MEDIUM] N+1 catastrófico no financial-report  (AP-201)
File: `src/AppManager.js:80-129`
Description: Para cada course (loop forEach) → busca enrollments; para cada enrollment → busca user e payment (2 queries). Cardinalidade O(C · E · 2). Com `Promise.all` ausente, ainda é sequencial via contadores manuais (`coursesPending`, `enrPending`).
Impact: Latência explode com volume; relatório em 100 cursos × 50 alunos = 10000 queries.
Recommendation: T-007 — uma query única com `JOIN` entre courses, enrollments, users, payments.

### [MEDIUM] APIs deprecated — Express 4 + sqlite3 callback-style  (DEPR-004, DEPR-005)
File: `package.json:11` (`"express": "^4.18.2"`), `src/AppManager.js:1` (`require('sqlite3').verbose()`)
Description: Express 5 já é estável (built-in `express.json()`, melhor handling de async); `sqlite3` callback-style é problemático — `better-sqlite3` é síncrono e ergonômico, `node:sqlite` é built-in no Node ≥ 22.
Impact: Travado em padrões antigos; difícil compor com async/await.
Recommendation: T-009 — atualizar para Express 5; migrar driver para `better-sqlite3` (ou `node:sqlite` se Node ≥ 22).

### [MEDIUM] Sem middlewares de segurança  (AP-202)
File: `src/app.js:1-14`
Description: Stack só inclui `express.json()`. Sem `helmet` (security headers), `cors` configurado, `express-rate-limit`, body-size limit, validação de input via `joi`/`zod`.
Impact: Vetores abertos: XSS via header, abuso, payload bomb.
Recommendation: Adicionar `helmet`, `cors` com whitelist via env, `express-rate-limit`, middleware `validate(schema)` para body.

### [MEDIUM] Validação superficial no checkout  (AP-202)
File: `src/AppManager.js:35`
Description: `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");` é toda a validação. Sem formato de email, sem Luhn no cartão, sem tamanho mínimo de senha, sem tipo do `c_id`.
Impact: Lixo no banco; erros opacos no service.
Recommendation: T-005 + schema `joi`/`zod` (`checkoutSchema`) aplicado por middleware antes do controller.

### [MEDIUM] Mistura `this.db` e `self.db` no mesmo handler  (AP-302)
File: `src/AppManager.js:26, 37, 50, 54, 57`
Description: O handler captura `self = this` na linha 26 mas alterna entre `this.db.get(...)` (linhas 37, 40, 50, 69) e `self.db.run(...)` (linhas 54, 57). Inconsistente.
Impact: Confusão de leitura; bug em refactor futuro.
Recommendation: Arrow functions (lexical `this`) ou usar instância via service.

### [LOW] Nomes ruins no body do checkout  (AP-302)
File: `src/AppManager.js:29-33`
Description: `let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;`
Impact: Code review caro; mistura confunde `e` (email) com `err`.
Recommendation: Destructuring com nomes plenos: `const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;`.

### [LOW] `let` para variáveis nunca reatribuídas  (AP-302)
File: `src/AppManager.js:29-33, 43, 46, 86, 90`
Description: Vários `let` para valores nunca reatribuídos. Sem `eslint`/`prefer-const`.
Impact: Sinal de hygiene baixa; `let` mascara intenção.
Recommendation: `const` por padrão; adicionar ESLint com `prefer-const`.

### [LOW] Idioma misturado nas mensagens  (AP-302)
File: `src/app.js:13` ("Frankenstein LMS rodando"), `src/AppManager.js:35` ("Bad Request"), `:38` ("Curso não encontrado"), `:41` ("Erro DB"), `:48` ("Pagamento recusado"), `:51` ("Erro Matrícula")
Description: Português e inglês alternados sem padrão; algumas mensagens internas, outras voltadas para usuário.
Impact: Inconsistência; tradução/i18n inviável; mistura de cliente vs interno.
Recommendation: Padronizar idioma; usar códigos de erro (`ERR_PAYMENT_DENIED`) e mensagem traduzida no cliente.

### [LOW] Magic strings de status  (AP-303)
File: `src/AppManager.js:46, 48, 54, 108`
Description: `"PAID"`, `"DENIED"` literais em vários pontos.
Impact: Typo silencioso quebra comparação.
Recommendation: T-010 — `const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' })`.

### [LOW] Export morto  (AP-205)
File: `src/utils.js:25`
Description: `totalRevenue` exportado, mas nenhum require/import consome.
Impact: Confusão; suggest que existe uma feature que não existe.
Recommendation: Remover do export.

## APIs Deprecated

| ID | Local | Equivalente moderno |
|---|---|---|
| DEPR-004 | `package.json:11` — `express ^4.18.2` | Express 5 (built-in `express.json()`, async handlers nativos). |
| DEPR-005 | `src/AppManager.js:1` — `require('sqlite3').verbose()` | `better-sqlite3` (síncrono, sem callback hell) ou `node:sqlite` (built-in Node ≥ 22). |

================================
Total: 21 findings
Summary: CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 5
Critical-or-High count: 11   (≥1 required by acceptance criteria)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
