# Analysis Heuristics — Detectar Linguagem, Framework, Banco e Domínio

Esta referência é usada na **Fase 1** da skill `refactor-arch`. Procedimento
mecânico para inspecionar um projeto desconhecido e extrair a stack.

---

## 1. Detecção de linguagem

| Sinal | Linguagem |
|---|---|
| `*.py` files + `requirements.txt`/`pyproject.toml`/`Pipfile` | Python |
| `*.js` ou `*.ts` files + `package.json` | Node.js |
| `*.go` + `go.mod` | Go |
| `*.rb` + `Gemfile` | Ruby |
| `pom.xml`/`build.gradle` + `*.java`/`*.kt` | Java/Kotlin |
| `*.php` + `composer.json` | PHP |
| `*.cs` + `*.csproj` | C#/.NET |

**Procedimento:**
1. `ls` o root do projeto.
2. Veja qual manifest de dependência existe.
3. Conte a maioria das extensões de fonte (ignorando `node_modules`, `venv`, `.git`).
4. A linguagem dominante é a do manifest + maior contagem.

---

## 2. Detecção de framework

### Python
Leia `requirements.txt` / `pyproject.toml` e procure por:

| Linha contém | Framework |
|---|---|
| `flask==X` ou `Flask==X` | Flask vX |
| `fastapi==X` | FastAPI vX |
| `django==X` ou `Django==X` | Django vX |
| `starlette` (sem fastapi) | Starlette |
| `tornado` | Tornado |
| `aiohttp` | aiohttp |
| `flask-sqlalchemy` | Flask + SQLAlchemy ORM |
| `sqlalchemy` (sem flask-sqlalchemy) | SQLAlchemy puro |
| `peewee` | Peewee |
| `marshmallow`/`pydantic` | validação |
| `flask-cors`/`flask-jwt-extended` | extensões Flask |

Se nenhum framework web aparecer, faça `grep -rn "from flask\|import flask\|from fastapi\|import fastapi\|django" .` para confirmar.

### Node.js
Leia `package.json` campo `dependencies`:

| Pacote | Framework |
|---|---|
| `express` | Express |
| `fastify` | Fastify |
| `koa` | Koa |
| `hapi`/`@hapi/hapi` | Hapi |
| `nestjs/core` | NestJS |
| `next` | Next.js |
| `restify` | Restify |
| `sqlite3` | SQLite driver callback-style |
| `better-sqlite3` | SQLite driver síncrono moderno |
| `pg`/`mysql2`/`mongodb` | Banco respectivo |
| `sequelize`/`typeorm`/`prisma` | ORM |

Sempre extraia a **versão exata** (incluindo o `^` ou `~`) para imprimir como `Express 4.18.2`.

---

## 3. Detecção de banco de dados

### Por código

```
grep -rn "sqlite3\.\|:memory:\|\.db['\"]" .   → SQLite
grep -rn "pymysql\|mysql\.connector\|mysql2"  → MySQL
grep -rn "psycopg\|asyncpg\|pg\." .            → PostgreSQL
grep -rn "pymongo\|mongoose\|mongodb"           → MongoDB
grep -rn "redis" .                              → Redis
```

### Por env
Procure por `DATABASE_URL`, `DB_HOST`, `MONGO_URI` em `.env*`, `os.environ`, `process.env`.

### Schema / tabelas
- SQL embedded: `grep -n "CREATE TABLE " *.py *.js *.sql` — extraia os nomes das tabelas.
- SQLAlchemy: arquivos em `models/` herdando de `db.Model` → o atributo `__tablename__` é o nome.
- Sequelize: `sequelize.define('name', ...)` ou classes em `models/`.
- Prisma: `schema.prisma` em `prisma/`.

Imprima a lista de tabelas/modelos na seção **DB tables**.

---

## 4. Detecção de domínio

Domínio = o que o app faz, em uma linha. Combine três sinais:

1. **Nome do projeto** (`name` em `package.json`, nome da pasta).
2. **Nomes das tabelas/models** — `produtos + pedidos + usuarios` → e-commerce; `tasks + categories + users` → task manager; `courses + enrollments + payments` → LMS.
3. **Rotas** — `grep -E "@app.route\|app.(get\|post\|put\|delete)" .` extrai os paths; `/api/checkout` reforça e-commerce, `/api/courses` reforça LMS.

Formato: `<Tipo de aplicação> (<entidades principais>)`.
Exemplo: `E-commerce API (produtos, pedidos, usuários)`.

Se a evidência for ambígua, prefira a interpretação mais defensiva e siga.

---

## 5. Detecção de arquitetura atual

Após detectar a stack, classifique o estado atual da estrutura:

| Sinal | Classificação |
|---|---|
| 1–5 arquivos no root, sem subpastas de domínio | **Monolítica plana** |
| Tem `models/` e `routes/` (ou `controllers/`) | **MVC parcial** |
| Tem `models/` + `controllers/` + `services/` + `middlewares/` | **MVC completo (pode precisar refinamento)** |
| Tem `domain/`, `application/`, `infrastructure/` | **Hexagonal/Clean (fora do escopo deste refactor)** |
| Há uma única classe ≥ 100 linhas misturando DB + rota + regra | **God Class** |
| Variáveis exportadas como mutáveis (cache, conexão) | adicione "estado global mutável" à descrição |

Imprima uma linha descritiva, ex.:
- `Monolítica — tudo em 4 arquivos, sem separação de camadas`
- `MVC parcial — blueprints + models, mas lógica de negócio nas rotas`
- `God Class (AppManager.js) — DB + rotas + pagamento + auditoria num único arquivo`

---

## 6. Contagem de arquivos

Conte **apenas** arquivos de código de aplicação. **Exclua sempre:**

- `node_modules/`, `venv/`, `.venv/`, `env/`
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.git/`, `.github/`
- `dist/`, `build/`, `coverage/`, `.next/`, `.cache/`
- arquivos gerados (`*.lock`, `*.lock.json`)
- migrations geradas automaticamente (`migrations/versions/*.py` no Alembic)

Inclua: fonte principal + entry point + módulos/blueprints + services + helpers.

Use um comando como:

```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "./node_modules/*" \
  -not -path "./venv/*" \
  -not -path "./.venv/*" \
  -not -path "./__pycache__/*" \
  -not -path "./.git/*" | wc -l
```

---

## 7. Output esperado (cole isso no resumo da Fase 1)

```
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
```

ou:

```
Language:      Node.js
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API (courses, enrollments, payments)
Architecture:  God Class (AppManager.js) — DB + rotas + checkout num único arquivo
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs
```
