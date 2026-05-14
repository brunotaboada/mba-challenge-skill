# Catálogo de Anti-Patterns

Referência usada na **Fase 2**. Cada anti-pattern tem:

- **ID** estável (use no relatório)
- **Severidade** (CRITICAL / HIGH / MEDIUM / LOW)
- **Sinais de detecção** — comandos grep/regex que você pode rodar
- **Por que importa** — uma frase
- **Como recomendar** — o que escrever no campo `Recommendation` do finding

Total: **17 anti-patterns** cobrindo segurança, arquitetura, performance, qualidade e APIs deprecated, com severidade distribuída em todas as 4 faixas (≥3 por faixa).

---

## CRITICAL

### AP-001 — Hardcoded Secrets
**Severidade:** CRITICAL
**Sinais:**
- `grep -nE "(SECRET_KEY|API_KEY|PASSWORD|TOKEN|GATEWAY_KEY)\s*[:=]\s*['\"]" .`
- Valores literais em `app.config[...]`, `process.env.* = "..."`, `const config = { ... key: "..." }`
**Por que:** segredo no histórico do Git é vazamento permanente; rotação não conserta repositórios já clonados.
**Recomendação:** mover para variável de ambiente (`os.environ.get("SECRET_KEY")` / `process.env.SECRET_KEY`); fornecer `.env.example`; nunca commitar `.env`.

### AP-002 — SQL Injection (concatenação)
**Severidade:** CRITICAL
**Sinais:**
- `grep -nE "execute\(['\"].*\+|run\(['\"].*\+|query\(['\"].*\+" .` (Python e Node)
- `grep -nE "execute\(['\"].*\{|query\(\`.*\$\{" .` (template strings)
- Procure `WHERE ... = '" + var` e similares.
**Por que:** input do usuário vira SQL executável — bypass de autenticação, dump de tabela, drop trivial.
**Recomendação:** sempre **parametrizar**: `cursor.execute("SELECT ... WHERE id = ?", (id,))` em Python; `?` placeholders em sqlite3 Node; ou usar o ORM (`User.query.filter_by(...)`, Sequelize, Prisma).

### AP-003 — Senhas em plaintext / hash quebrado
**Severidade:** CRITICAL
**Sinais:**
- `grep -nE "senha\s+TEXT|password\s+TEXT" .` (schema sem hash)
- `grep -n "hashlib\.md5\|hashlib\.sha1\|crypto\.createHash\(['\"]md5" .`
- `INSERT INTO users.*VALUES.*'<literal-password>'` no seed.
- `cursor.execute("... senha = '" + senha + "'")` — sinal de comparação direta.
**Por que:** vazamento de DB = vazamento de credenciais. MD5/SHA1 quebrados desde 2005/2017.
**Recomendação:** usar `bcrypt`, `argon2` ou `scrypt` com salt; nunca armazenar plaintext; nunca usar `hashlib.md5` para senha.

### AP-004 — Dados sensíveis vazando na resposta
**Severidade:** CRITICAL
**Sinais:**
- `grep -nE "\"(senha|password|secret_key|api_key|token|cvv|card_number)\":" .` em `jsonify`/`res.json`
- Funções `to_dict()` que retornam o campo de senha (mesmo que hasheado).
**Por que:** API expõe credenciais para qualquer cliente do front (DevTools).
**Recomendação:** remover do `to_dict()`/serializer; criar um DTO/schema explícito para resposta.

### AP-005 — SQL arbitrário ou DB-wipe sem autenticação
**Severidade:** CRITICAL
**Sinais:**
- Endpoints chamando `cursor.execute(request_body)` direto.
- Endpoints `/reset-db`, `/admin/query`, `/debug/sql` sem checagem de papel/auth.
**Por que:** SQLi-as-a-service. Compromisso total do banco com uma requisição.
**Recomendação:** **remover** o endpoint. Se realmente precisar, fechar atrás de auth+role+IP whitelist e logar cada execução. Para reset em dev, usar comando CLI separado, não rota HTTP.

### AP-006 — Logs com dado sensível (PCI/PII)
**Severidade:** CRITICAL
**Sinais:**
- `grep -nE "(console\.log|print).*card|cartão|cvv|senha|password|secret" .`
**Por que:** logs vão para arquivo, ELK, stdout do container — dado sensível com retenção indefinida.
**Recomendação:** mascarar (`****-****-****-1234`) ou nunca logar; usar `logging.getLogger().setLevel(INFO)` com filtros que redacionam campos sensíveis.

---

## HIGH

### AP-101 — God Class / God Module
**Severidade:** HIGH
**Sinais:**
- Arquivo de aplicação único com > ~250 linhas misturando responsabilidades.
- Classe única que faz: DB schema + rotas + regra de negócio.
- `wc -l *.py *.js` mostra arquivos com 300+ linhas no root.
**Por que:** qualquer mudança afeta tudo; impossível testar em isolamento; merge conflicts contínuos.
**Recomendação:** separar em camadas: `models/`, `controllers/`, `services/`, `routes/`. Uma classe/módulo por entidade.

### AP-102 — Estado global mutável
**Severidade:** HIGH
**Sinais:**
- Variáveis de módulo reatribuídas (`db_connection = None` → reatribui em função).
- Caches exportados: `let globalCache = {}` exportado.
- `check_same_thread=False` em sqlite3 com singleton.
**Por que:** comportamento depende de ordem de requests; race conditions; impossível paralelizar.
**Recomendação:** encapsular em factory/connection pool; usar `g`/`current_app` no Flask; em Node, usar middleware de request-scoped container.

### AP-103 — Fat Controller (lógica de negócio em rota/handler)
**Severidade:** HIGH
**Sinais:**
- Handler de rota com > ~30 linhas.
- Loops, agregações, formatação dentro do `def route_handler` ou `app.get(...)`.
- Side-effects (email, log, payment) dentro do handler.
**Por que:** controller deveria ser plumbing (request → service → response). Quando vira "service", testes ficam acoplados ao Flask/Express.
**Recomendação:** extrair para `services/<dominio>_service.py` ou `.js`; controller fica com no máximo: parse input → service.do(...) → jsonify result.

### AP-104 — Falta de transação em operação multi-step
**Severidade:** HIGH
**Sinais:**
- Múltiplos `INSERT/UPDATE` no mesmo handler sem `BEGIN/COMMIT` ou `session.begin()`.
- Callbacks aninhados encadeando inserts (Node).
- Operação de pedido/checkout que escreve em 3+ tabelas sem rollback no erro.
**Por que:** se uma etapa falhar, dados ficam inconsistentes (pedido criado sem itens, pagamento sem matrícula).
**Recomendação:** envolver em `with db.session.begin():` (SQLAlchemy), `BEGIN ... COMMIT` (sqlite raw), ou usar `db.serialize` + transação explícita no Node.

### AP-105 — Validação duplicada (DRY)
**Severidade:** HIGH
**Sinais:**
- Mesmo bloco `if not data... return jsonify({"erro": "Campo obrigatório"})` em `create_*` e `update_*`.
- Regex de email repetida em vários arquivos.
- Função `is_overdue` reimplementada em models, controllers e reports.
**Por que:** mudar regra de validação requer mudar N lugares; quase certo que algum vai ficar fora de sincronia.
**Recomendação:** extrair para `utils/validators.py` / `middlewares/validate.js`, ou usar schema (`marshmallow`, `pydantic`, `joi`, `zod`).

### AP-106 — Exceção engolida (`except:` / `catch (_) {}`)
**Severidade:** HIGH
**Sinais:**
- `grep -n "except:" .` (bare except em Python)
- `grep -n "} catch (\(_\)\?) {" .` (Node)
- Handlers que sempre retornam 500 genérico sem logar.
**Por que:** mascara bug; em Python, `except:` também pega `KeyboardInterrupt` e `SystemExit`.
**Recomendação:** capturar exceções específicas; **logar** com stack trace; deixar exceção genérica subir para o error handler centralizado.

### AP-107 — DEBUG / CORS aberto em produção
**Severidade:** HIGH
**Sinais:**
- `app.config["DEBUG"] = True`
- `app.run(debug=True)`
- `CORS(app)` sem `origins=`
**Por que:** DEBUG=True expõe stack trace e console de execução. CORS aberto permite qualquer site fazer fetch autenticado.
**Recomendação:** ler `DEBUG` de env (`DEBUG=os.environ.get("FLASK_DEBUG") == "1"`); CORS com `origins=os.environ.get("ALLOWED_ORIGINS", "").split(",")`.

### AP-108 — Service sem injeção de dependência
**Severidade:** HIGH
**Sinais:**
- Classe de service instanciada **dentro** de cada handler.
- Credenciais lidas no `__init__` da classe, sem passar como parâmetro.
- Service importado mas nunca usado.
**Por que:** impossível mockar em teste; rebinding de config requer restart.
**Recomendação:** registrar service no composition root, injetar via construtor/parâmetro; permitir overrides em teste.

---

## MEDIUM

### AP-201 — N+1 Query
**Severidade:** MEDIUM
**Sinais:**
- `for ... in records: <segunda query>` em Python.
- `forEach` aninhado fazendo queries em Node.
- Listagem que enriquece resultado com lookup item-a-item.
**Por que:** latência cresce linearmente com tamanho do resultado; queries explodem.
**Recomendação:** usar `JOIN` na query principal, `joinedload`/`selectinload` no SQLAlchemy, `include` no Sequelize/Prisma, ou um único `WHERE id IN (...)`.

### AP-202 — Validação ausente em endpoint
**Severidade:** MEDIUM
**Sinais:**
- `request.get_json()` direto em `models.criar_*(...)` sem checar tipo/formato.
- `req.body.field` usado sem verificar undefined.
- Campos email/CPF/data sem regex/parse.
**Por que:** valida na borda evita lixo no banco e erros opacos no service.
**Recomendação:** schema central (`marshmallow`/`pydantic`/`joi`/`zod`) ou middleware de validação.

### AP-203 — Magic numbers / constantes inline
**Severidade:** MEDIUM
**Sinais:**
- Faixas de prioridade `1..5` hardcoded em 4 lugares.
- `if faturamento > 10000: desconto = 0.1` em meio a uma função.
- `MIN_PASSWORD_LENGTH = 4` (sem justificativa, em arquivo de helper).
**Por que:** mudar regra de negócio sem grep abrangente é arriscado.
**Recomendação:** mover para `config/constants.py`/`config/constants.js` ou `Enum`.

### AP-204 — Mistura de responsabilidades entre módulos
**Severidade:** MEDIUM
**Sinais:**
- CRUD de uma entidade dentro do blueprint/router de outra (ex: `/categories` dentro de `report_routes.py`).
- Função "helper" que tanto valida quanto transforma.
**Por que:** dificulta encontrar onde algo mora; viola SRP.
**Recomendação:** reorganizar por domínio; criar `category_routes.py` separado.

### AP-205 — Imports não usados
**Severidade:** MEDIUM
**Sinais:**
- `grep -nE "^import (os|sys|json|time|math)$" .` e cross-check se o módulo é usado.
- Sinal de copy-paste e ausência de linter.
**Por que:** indica baixa hygiene; em projetos maiores camufla acoplamento real.
**Recomendação:** rodar `ruff`/`flake8`/`eslint` e remover; adicionar pre-commit hook.

### AP-206 — `db.create_all()` no boot sem migrations
**Severidade:** MEDIUM
**Sinais:**
- `with app.app_context(): db.create_all()` em `app.py`.
- Ausência de `migrations/` ou `alembic.ini`.
**Por que:** schema diverge silenciosamente entre dev/staging/prod; rename de coluna não roda.
**Recomendação:** `flask-migrate`/`alembic` (Python) ou `umzug`/`prisma migrate` (Node).

---

## LOW

### AP-301 — `print` / `console.log` como logging
**Severidade:** LOW
**Sinais:**
- `grep -nE "^[^#]*print\(" *.py`
- `grep -n "console.log" src/`
- Sem `import logging`, sem `winston`/`pino`.
**Por que:** sem níveis (DEBUG/INFO/WARN/ERROR), sem destino configurável, sem formato estruturado.
**Recomendação:** `logging.getLogger(__name__)` em Python; `pino`/`winston` em Node.

### AP-302 — Nomes ruins / variáveis de uma letra
**Severidade:** LOW
**Sinais:**
- `let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd;` no checkout.
- Funções `f(a, b)`.
**Por que:** legibilidade baixa, code review caro.
**Recomendação:** nomes plenos (`user`, `email`, `password`); destructuring com nome legível.

### AP-303 — Magic strings de status / enums faltando
**Severidade:** LOW
**Sinais:**
- Strings `'pending'`, `'done'`, `'PAID'`, `'DENIED'` repetidas em 5+ lugares sem constante.
**Por que:** typo em um lugar não é detectado pelo compilador/runtime.
**Recomendação:** `from enum import Enum` ou `const STATUS = Object.freeze({...})`.

---

## APIs DEPRECATED — Detecção obrigatória

Esta seção é **sempre** incluída no relatório (mesmo se vazia, reporte "nenhuma detectada").

### DEPR-001 — `datetime.utcnow()` (Python ≥ 3.12)
**Sinais:** `grep -nE "datetime\.utcnow\(\)" .`
**Equivalente moderno:** `datetime.now(timezone.utc)` (com `from datetime import timezone`).

### DEPR-002 — `Model.query.get(id)` (SQLAlchemy 2.0+)
**Sinais:** `grep -nE "\.query\.get\(" .`
**Equivalente moderno:** `db.session.get(Model, id)`.

### DEPR-003 — `Flask.before_first_request` (Flask 2.3+)
**Sinais:** `grep -n "before_first_request" .`
**Equivalente moderno:** chamar o setup uma única vez antes do `app.run()` (dentro de `if __name__ == "__main__"`).

### DEPR-004 — Express 4.x callback-style + `body-parser` separado (Express 5 estável)
**Sinais:** `express ^4` em `package.json`; `app.use(bodyParser.json())`.
**Equivalente moderno:** Express 5; `app.use(express.json())` já é built-in.

### DEPR-005 — `sqlite3.verbose()` callback-style (Node)
**Sinais:** `require('sqlite3').verbose()`.
**Equivalente moderno:** `better-sqlite3` (síncrono, sem callback hell) ou `node:sqlite` (built-in no Node ≥ 22).

### DEPR-006 — `hashlib.md5` / `hashlib.sha1` para senha
Já coberto por AP-003 mas reportar **também** aqui como deprecated.

### DEPR-007 — `type(x) == list` em Python
**Sinais:** `grep -nE "type\([^)]+\) ==" .`
**Equivalente moderno:** `isinstance(x, list)`.

---

## Como usar este catálogo na Fase 2

1. Para cada AP-* / DEPR-*, rode o comando de detecção.
2. Para cada match, abra o arquivo, valide que **é mesmo** o anti-pattern (evita falso positivo) e registre arquivo:linha exatos.
3. Numere os findings começando em 1, ordenados por severidade.
4. **Sempre** inclua a subseção "APIs deprecated" no relatório, mesmo se vazia.
5. Use o ID estável (AP-001, DEPR-002, etc.) no campo `Category` do finding para que a Fase 3 saiba qual transformação do playbook aplicar.
