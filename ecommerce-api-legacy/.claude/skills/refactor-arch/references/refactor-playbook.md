# Refactor Playbook — Transformações com Antes/Depois

Para cada anti-pattern do catálogo, um padrão concreto de transformação.
Use os IDs `AP-*`/`DEPR-*` para mapear finding → transformação.

Total: **10 transformações** cobrindo todos os anti-patterns do catálogo.
Exemplos em Python/Flask e Node.js/Express para garantir agnosticismo.

---

## T-001 — Extract Config (AP-001, AP-107)

**Quando:** segredo hardcoded, DEBUG=True, CORS aberto.

### Antes (Python)
```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
```

### Depois (Python)
```python
# src/config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    ALLOWED_ORIGINS = os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")

settings = Settings()

# app.py
from flask_cors import CORS
from src.config.settings import settings

app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
CORS(app, origins=settings.ALLOWED_ORIGINS)
```

### Antes (Node)
```javascript
const config = { dbPass: "senha123", paymentGatewayKey: "pk_live_..." };
```

### Depois (Node)
```javascript
// src/config/index.js
require('dotenv').config();

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  allowedOrigins: (process.env.ALLOWED_ORIGINS || '').split(',').filter(Boolean),
};

if (!module.exports.paymentGatewayKey) {
  throw new Error('PAYMENT_GATEWAY_KEY env var is required');
}
```

**Sempre gere também um `.env.example`** com os nomes (não os valores).

---

## T-002 — Parametrize SQL (AP-002)

**Quando:** SQL via concatenação.

### Antes
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

### Depois
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute(
    "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
    (email, senha_hash),
)
```

### Node (Antes / Depois)
```javascript
// Antes
db.run(`INSERT INTO users (name, email) VALUES ('${name}', '${email}')`);

// Depois
db.run("INSERT INTO users (name, email) VALUES (?, ?)", [name, email]);
```

**Regra:** input do usuário **nunca** entra na string SQL. Se a query for
dinâmica (filtros opcionais), construa a lista de placeholders e a lista de
args em paralelo:

```python
filters = ["1=1"]
params = []
if termo:
    filters.append("(nome LIKE ? OR descricao LIKE ?)")
    params.extend([f"%{termo}%", f"%{termo}%"])
if categoria:
    filters.append("categoria = ?")
    params.append(categoria)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(filters)}", params)
```

---

## T-003 — Replace MD5/Plaintext with bcrypt (AP-003, DEPR-006)

**Quando:** senha em plaintext, MD5, SHA1, base64 ou similar.

### Antes
```python
# models/user.py
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### Depois
```python
# requirements.txt: bcrypt==4.x
import bcrypt

def set_password(self, pwd: str) -> None:
    self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_password(self, pwd: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), self.password.encode())
```

### Node (Antes / Depois)
```javascript
// Antes — badCrypto
function badCrypto(pwd) {
  let hash = "";
  for (let i = 0; i < 10000; i++) {
    hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  }
  return hash.substring(0, 10);
}

// Depois — bcrypt
const bcrypt = require('bcrypt');
async function hashPassword(pwd) {
  return bcrypt.hash(pwd, 10);
}
async function checkPassword(pwd, hash) {
  return bcrypt.compare(pwd, hash);
}
```

**Importante:** ao migrar, senhas antigas armazenadas em MD5 não voltam.
Documente que usuários precisarão de "esqueci minha senha" no primeiro login,
ou faça migração com double-hash (`bcrypt(md5(pwd))`).

---

## T-004 — Strip Sensitive Fields from Response (AP-004)

**Quando:** `to_dict()` ou resposta JSON retorna campo de senha/segredo.

### Antes
```python
# models/user.py
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,   # ← vazamento
        'role': self.role,
    }
```

### Depois
```python
# models/user.py
def to_dict(self) -> dict:
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        'active': self.active,
    }
```

### Health endpoint (Antes / Depois)
```python
# Antes
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123",
    "db_path": "loja.db",
})

# Depois
return jsonify({"status": "ok", "version": settings.VERSION})
```

**Regra:** nunca exponha `password`, `secret_key`, `api_key`, `db_path`,
`internal_token` em response — mesmo em health checks.

---

## T-005 — Extract Service from Fat Controller (AP-101, AP-103, AP-108)

**Quando:** controller > 30 linhas; God Class; lógica de domínio em rota.

### Antes (controller monstruoso)
```python
# controllers.py
def criar_pedido():
    dados = request.get_json()
    # ... validação
    total = 0
    for item in itens:
        produto = models.get_produto(item["produto_id"])
        if produto["estoque"] < item["quantidade"]:
            return jsonify({"erro": "Estoque insuficiente"}), 400
        total += produto["preco"] * item["quantidade"]
    pedido_id = models.criar_pedido(usuario_id, total)
    for item in itens:
        models.adicionar_item(pedido_id, item)
        models.decrementar_estoque(item)
    print("ENVIANDO EMAIL")
    return jsonify({"pedido_id": pedido_id, "total": total}), 201
```

### Depois (camadas separadas)
```python
# services/pedido_service.py
class PedidoService:
    def __init__(self, produto_repo, pedido_repo, notifier):
        self.produto_repo = produto_repo
        self.pedido_repo = pedido_repo
        self.notifier = notifier

    def criar(self, usuario_id: int, itens: list) -> dict:
        total = self._calcular_total(itens)
        with self.pedido_repo.transaction():
            pedido_id = self.pedido_repo.criar(usuario_id, total)
            for item in itens:
                self.pedido_repo.adicionar_item(pedido_id, item)
                self.produto_repo.decrementar_estoque(
                    item["produto_id"], item["quantidade"]
                )
        self.notifier.notify_pedido_criado(usuario_id, pedido_id)
        return {"pedido_id": pedido_id, "total": total}

    def _calcular_total(self, itens):
        total = 0
        for item in itens:
            produto = self.produto_repo.get(item["produto_id"])
            if produto["estoque"] < item["quantidade"]:
                raise EstoqueInsuficienteError(produto["nome"])
            total += produto["preco"] * item["quantidade"]
        return total

# controllers/pedido_controller.py
def criar_pedido(pedido_service):
    def handler():
        dados = request.get_json()
        try:
            resultado = pedido_service.criar(dados["usuario_id"], dados["itens"])
            return jsonify({"dados": resultado, "sucesso": True}), 201
        except EstoqueInsuficienteError as e:
            return jsonify({"erro": str(e)}), 400
    return handler
```

Composition root:
```python
# app.py
from src.services.pedido_service import PedidoService
from src.controllers import pedido_controller

pedido_service = PedidoService(produto_repo, pedido_repo, notifier)
app.add_url_rule(
    "/pedidos", "criar_pedido",
    pedido_controller.criar_pedido(pedido_service), methods=["POST"]
)
```

---

## T-006 — Wrap Multi-step Writes in Transaction (AP-104)

**Quando:** múltiplos INSERT/UPDATE encadeados sem rollback.

### Antes (Python/sqlite3)
```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()
```

### Depois (Python/sqlite3)
```python
try:
    cursor.execute("BEGIN")
    cursor.execute("INSERT INTO pedidos ...", (...))
    pedido_id = cursor.lastrowid
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido ...", (...))
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )
    db.commit()
except Exception:
    db.rollback()
    raise
```

### Python/SQLAlchemy
```python
# Antes
db.session.add(task)
db.session.commit()

# Depois (operação multi-step)
try:
    with db.session.begin():
        db.session.add(pedido)
        for item in itens:
            db.session.add(ItemPedido(...))
            produto = db.session.get(Produto, item["produto_id"])
            produto.estoque -= item["quantidade"]
except IntegrityError:
    raise EstoqueInsuficienteError(...)
```

### Node (sqlite3)
```javascript
db.serialize(() => {
  db.run("BEGIN TRANSACTION");
  db.run("INSERT INTO enrollments ...", [...], (err) => {
    if (err) return db.run("ROLLBACK", () => next(err));
    db.run("INSERT INTO payments ...", [...], (err) => {
      if (err) return db.run("ROLLBACK", () => next(err));
      db.run("COMMIT");
    });
  });
});
```

Ou, melhor, use `better-sqlite3` (síncrono, com `db.transaction(...)`):
```javascript
const checkout = db.transaction((data) => {
  const enrId = db.prepare("INSERT INTO enrollments ...").run(...).lastInsertRowid;
  db.prepare("INSERT INTO payments ...").run(enrId, ...);
});
checkout(data);
```

---

## T-007 — Resolve N+1 (AP-201)

**Quando:** loop sobre resultado fazendo query por item.

### Antes (Python)
```python
def get_todos_pedidos():
    cursor.execute("SELECT * FROM pedidos")
    for row in cursor.fetchall():
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
        for item in cursor2.fetchall():
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
            ...
```

### Depois — JOIN único
```python
def get_todos_pedidos():
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
            ip.produto_id, ip.quantidade, ip.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        ORDER BY p.id
    """)
    pedidos = {}
    for row in cursor.fetchall():
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid, "usuario_id": row["usuario_id"],
                "status": row["status"], "total": row["total"],
                "criado_em": row["criado_em"], "itens": [],
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())
```

### SQLAlchemy (Antes / Depois)
```python
# Antes
for task in Task.query.all():
    user = User.query.get(task.user_id)
    cat = Category.query.get(task.category_id)

# Depois — eager loading
from sqlalchemy.orm import joinedload
tasks = Task.query.options(
    joinedload(Task.user),
    joinedload(Task.category),
).all()
```

---

## T-008 — Replace Bare Except / Empty Catch (AP-106)

**Quando:** `except:` ou `} catch (_) {}` engolindo erro.

### Antes
```python
try:
    tasks = Task.query.all()
    ...
except:
    return jsonify({'error': 'Erro interno'}), 500
```

### Depois — error handler centralizado
```python
# middlewares/error_handler.py
import logging
from werkzeug.exceptions import HTTPException
log = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def http_error(e):
        return {"error": e.description}, e.code

    @app.errorhandler(DomainError)         # exceções do seu domínio
    def domain_error(e):
        return {"error": str(e)}, 400

    @app.errorhandler(Exception)
    def unhandled(e):
        log.exception("Unhandled exception")
        return {"error": "Internal server error"}, 500

# controllers/task_controller.py
def get_tasks():
    tasks = task_service.list_all()
    return jsonify(tasks), 200          # sem try/except. erros sobem.
```

### Node
```javascript
// Antes
app.get('/tasks', (req, res) => {
  db.all("SELECT ...", (err, rows) => {
    if (err) res.status(500).send("Erro");
    else res.json(rows);
  });
});

// Depois
app.get('/tasks', asyncHandler(async (req, res) => {
  const tasks = await taskService.listAll();
  res.json(tasks);
}));

// middlewares/errorHandler.js
module.exports = (err, req, res, _next) => {
  req.log?.error(err);
  if (err.statusCode) return res.status(err.statusCode).json({ error: err.message });
  res.status(500).json({ error: 'Internal server error' });
};
```

---

## T-009 — Modernize Deprecated APIs (DEPR-001..007)

### DEPR-001 — `datetime.utcnow()`
```python
# Antes
from datetime import datetime
created_at = datetime.utcnow()

# Depois
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

Em SQLAlchemy `default=`:
```python
# Antes
created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Depois
created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### DEPR-002 — `Model.query.get(id)`
```python
# Antes
user = User.query.get(user_id)

# Depois
user = db.session.get(User, user_id)
```

### DEPR-004 — Express 4 → 5 + `body-parser`
```javascript
// package.json
- "express": "^4.18.2",
+ "express": "^5.0.0",

// código
- const bodyParser = require('body-parser');
- app.use(bodyParser.json());
+ app.use(express.json());
```

### DEPR-005 — sqlite3 callback-style → better-sqlite3
```javascript
// Antes
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database(':memory:');
db.all("SELECT ...", [], (err, rows) => { ... });

// Depois
const Database = require('better-sqlite3');
const db = new Database(':memory:');
const rows = db.prepare("SELECT ...").all();
```

### DEPR-007 — `type(x) == list`
```python
# Antes
if type(tags) == list:

# Depois
if isinstance(tags, list):
```

---

## T-010 — Centralize Logging + Constants (AP-203, AP-301, AP-303)

**Quando:** `print()`/`console.log` espalhados, magic numbers/strings.

### Logging em Python
```python
# Antes
print("Usuário criado: " + email)

# Depois
import logging
log = logging.getLogger(__name__)
log.info("Usuário criado", extra={"email": email})

# app.py — configurar uma vez
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```

### Logging em Node
```javascript
// Antes
console.log("Login bem-sucedido");

// Depois
const pino = require('pino');
const log = pino({ level: process.env.LOG_LEVEL || 'info' });
log.info({ userId }, "Login successful");
```

### Constants e Enums (Python)
```python
# Antes — espalhado
if status not in ['pending', 'in_progress', 'done', 'cancelled']:

# Depois
# src/config/constants.py
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

# uso
if status not in TaskStatus.__members__.values():
```

### Constants em Node
```javascript
// src/config/constants.js
const TASK_STATUS = Object.freeze({
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  DONE: 'done',
  CANCELLED: 'cancelled',
});

const PAYMENT_STATUS = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

module.exports = { TASK_STATUS, PAYMENT_STATUS };
```

---

## Mapa Anti-Pattern → Transformação

| Catálogo | Transformação |
|---|---|
| AP-001 Hardcoded Secrets | T-001 |
| AP-002 SQL Injection | T-002 |
| AP-003 Plaintext/MD5 password | T-003 |
| AP-004 Sensitive in response | T-004 |
| AP-005 SQL arbitrário sem auth | T-001 + **remover endpoint** |
| AP-006 Log PCI/PII | T-010 (logging com redaction) |
| AP-101 God Class/Module | T-005 |
| AP-102 Mutable global state | T-005 (composition root) |
| AP-103 Fat Controller | T-005 |
| AP-104 Missing transaction | T-006 |
| AP-105 DRY violation | T-005 (service compartilhado) ou utils |
| AP-106 Bare except | T-008 |
| AP-107 DEBUG/CORS aberto | T-001 |
| AP-108 Service sem DI | T-005 (composition root injeta deps) |
| AP-201 N+1 | T-007 |
| AP-202 Validação ausente | T-005 + schema (marshmallow/zod) |
| AP-203 Magic numbers | T-010 |
| AP-204 Mistura de domínios | T-005 (split blueprint/router) |
| AP-205 Imports não usados | linter (ruff/eslint) |
| AP-206 db.create_all | adicionar Alembic/Umzug (TODO) |
| AP-301 print logging | T-010 |
| AP-302 Nomes ruins | rename simples |
| AP-303 Magic strings | T-010 |
| DEPR-001..007 | T-009 |

---

## Ordem de aplicação na Fase 3

1. **T-001** (config) — antes de qualquer coisa, para que nada novo use literal.
2. **T-009** (deprecated APIs) — fix de baixo risco que destrava modernização.
3. **T-002, T-003, T-004** (segurança) — fechar o vetor crítico imediatamente.
4. **T-005** (extract service/controller) — reestruturação maior, vem depois que segurança e config estão estáveis.
5. **T-006** (transação) — em cima de T-005 (service já existe).
6. **T-007** (N+1) — geralmente vai junto com T-005.
7. **T-008** (error handler) — depois que controllers existem.
8. **T-010** (logging/constants) — polimento final.
