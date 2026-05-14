================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLAlchemy 3.1.1)
Files:   12 analyzed | ~1000 lines of code
Date:    2026-05-14

## Phase 1 — Project Analysis

```
Language:      Python
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0
Domain:        Task Manager API (users, categories, tasks)
Architecture:  MVC parcial — possui models/, routes/ (blueprints), services/, utils/,
               mas lógica de negócio mora nas rotas; services não são injetados.
Source files:  12 files analyzed
DB tables:     tasks, users, categories
```

Endpoints detectados:
- `GET /`, `GET /health`
- `GET /tasks`, `GET /tasks/<id>`, `POST /tasks`, `PUT /tasks/<id>`, `DELETE /tasks/<id>`
- `GET /tasks/search`, `GET /tasks/stats`
- `GET /users`, `GET /users/<id>`, `POST /users`, `PUT /users/<id>`, `DELETE /users/<id>`
- `GET /users/<id>/tasks`, `POST /login`
- `GET /reports/summary`, `GET /reports/user/<id>`
- `GET /categories`, `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>`

## Summary

| Severidade | Quantidade |
|---|---|
| CRITICAL | 5 |
| HIGH     | 5 |
| MEDIUM   | 5 |
| LOW      | 6 |
| **Total**| **21** |

Critical-or-High count: 10 (≥1 required by acceptance criteria) ✓

## Findings

### [CRITICAL] Hardcoded Secret  (AP-001)
File: `app.py:13`
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` no código.
Impact: Segredo permanente no Git; permite forjar tokens (mesmo que o app use "fake JWT", outras integrações podem depender disso).
Recommendation: T-001 — `os.environ.get("SECRET_KEY")` + `.env.example`.

### [CRITICAL] Hash MD5 para senha sem salt  (AP-003, DEPR-006)
File: `models/user.py:29`, `models/user.py:32`
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`. MD5 é criptograficamente quebrado desde 2004; sem salt, vazamentos viram brute-force imediato com rainbow tables.
Impact: Hash do banco é trivial de reverter para a maioria das senhas.
Recommendation: T-003 — `bcrypt.hashpw` / `bcrypt.checkpw`. Documentar reset de senha para usuários existentes.

### [CRITICAL] Credenciais SMTP hardcoded  (AP-001)
File: `services/notification_service.py:8-11`
Description: `self.email_host = 'smtp.gmail.com'`, `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`.
Impact: Conta de email comprometida com `git clone` do repo.
Recommendation: T-001 — variáveis de ambiente + DI no construtor (`NotificationService(host, user, password)`).

### [CRITICAL] Senha (hash MD5) exposta no JSON  (AP-004)
File: `models/user.py:17-25`
Description: `User.to_dict()` retorna `'password': self.password`. O hash MD5 cai no body de `GET /users/<id>`, `POST /users`, `PUT /users/<id>`, `POST /login`.
Impact: Vazamento do hash facilita ataque de rainbow table; usuários veem o hash de outros (em GET /users/<id> aplicado a outro).
Recommendation: T-004 — remover `password` do `to_dict()`; criar serializer/schema explícito.

### [CRITICAL] "JWT" falso no login  (AP-202)
File: `routes/user_routes.py:210`
Description: `'token': 'fake-jwt-token-' + str(user.id)` — qualquer um pode forjar o token de qualquer usuário com `fake-jwt-token-1`.
Impact: Autenticação completamente quebrada; toda autorização baseada nesse token é trivial de bypassar.
Recommendation: Adotar `flask-jwt-extended` ou `PyJWT` com `SECRET_KEY` do env; assinar JWT real com claims (sub, iat, exp).

### [HIGH] Fat Controllers — lógica de negócio nas rotas  (AP-103)
File: `routes/task_routes.py:12-63` (`get_tasks`), `routes/report_routes.py:13-101` (`summary_report`), `routes/user_routes.py:42-90` (`create_user`)
Description: `get_tasks` calcula overdue, enriquece com nome de user/category e formata, tudo em 50 linhas dentro do handler. `summary_report` faz toda a agregação inline. `create_user` mistura validação, persistência e logging.
Impact: Impossível testar agregação/regras sem subir Flask; reuso entre rotas impossível.
Recommendation: T-005 — `services/task_service.py` (overdue, stats), `services/report_service.py` (agregação); controllers ficam ≤ 20 linhas cada.

### [HIGH] Bare `except:` engole erros  (AP-106)
File: `routes/task_routes.py:62, 137, 204, 236`; `routes/user_routes.py:130, 150`; `routes/report_routes.py:186, 208, 222`
Description: 9 ocorrências de `except:` sem tipo. Em Python isso pega também `KeyboardInterrupt` e `SystemExit`; em todos os casos o tratamento é só `return jsonify({'error': '...'}), 500` sem log do stack trace.
Impact: Bugs invisíveis; impossível debugar em produção.
Recommendation: T-008 — error handler centralizado em `middlewares/error_handler.py`; controllers sem try/except, deixam exceções subirem.

### [HIGH] Lógica `is_overdue` duplicada em 4 lugares  (AP-105)
File: `models/task.py:50-60`, `routes/task_routes.py:30-39, 71-80`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-43`
Description: Cálculo `if due_date and due_date < now and status not in ('done','cancelled')` reescrito 4 vezes (com pequenas variações de indentação).
Impact: Mudança de regra de "overdue" requer mudar em 4 lugares; alta chance de inconsistência.
Recommendation: T-005 — centralizar em `Task.is_overdue()` (já existe no model!) e usar a partir das demais camadas; eliminar reimplementações inline.

### [HIGH] Blueprint de Categories no lugar errado  (AP-204)
File: `routes/report_routes.py:157-223`
Description: `GET/POST/PUT/DELETE /categories` mora dentro do blueprint `reports`. Domínio errado.
Impact: Maintainer novo procura `/categories` em `routes/report_routes.py`? Improvável. Risco de duplicar.
Recommendation: Criar `routes/category_routes.py` + `controllers/category_controller.py`.

### [HIGH] NotificationService sem DI e nunca usado  (AP-108)
File: `services/notification_service.py:1-48`
Description: Classe `NotificationService` está implementada (envia email via SMTP), mas **nenhum** lugar do código a importa ou instancia. Configuração SMTP fica hardcoded no `__init__`.
Impact: Código morto + segredos no fonte. Quando alguém for ligar, vai instanciar errado.
Recommendation: T-005 — receber config no construtor; registrar singleton no composition root; injetar nos services que precisam (task_service quando assign/overdue).

### [MEDIUM] N+1 em listagem de tasks  (AP-201)
File: `routes/task_routes.py:41-58`
Description: Para cada task, chama `User.query.get(t.user_id)` e `Category.query.get(t.category_id)`. Com 100 tasks → 201 queries.
Impact: Latência cresce linearmente; SQLite tolera, Postgres com latência de rede explode.
Recommendation: T-007 — `Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()`.

### [MEDIUM] N+1 em relatório de produtividade  (AP-201)
File: `routes/report_routes.py:54-68`
Description: `user_productivity` loop: para cada user, `Task.query.filter_by(user_id=u.id).all()` — N+1 clássico.
Impact: Relatório com N usuários = N+1 queries.
Recommendation: T-007 — uma query agrupada por `user_id`, ou `selectinload` no modelo User.

### [MEDIUM] Validação ad-hoc (sem marshmallow)  (AP-202, AP-105)
File: `routes/task_routes.py:86-145, 156-223`; `routes/user_routes.py:46-78, 92-132`
Description: Validação de payload manual com `if not data... return jsonify(...)`. Lógica espalhada e repetida entre create e update. `marshmallow` está em `requirements.txt` mas não é usado.
Impact: Mudar formato exige editar 2-3 lugares; mensagens inconsistentes.
Recommendation: T-005 — `schemas/task_schema.py` com marshmallow, decorator `@validate_with(schema)` no controller.

### [MEDIUM] Imports não usados  (AP-205)
File: `routes/task_routes.py:7` (`os, sys, json, time`), `routes/user_routes.py:6` (`hashlib, json`), `utils/helpers.py:4-7` (`os, sys, json, math`)
Description: Vários imports nunca referenciados nos arquivos. Sinal de copy-paste de boilerplate e ausência de linter.
Impact: Baixa hygiene; mascara dependências reais.
Recommendation: Rodar `ruff check --fix .` ou `flake8 + autoflake`; adicionar pre-commit hook.

### [MEDIUM] `db.create_all()` no boot sem migrations  (AP-206)
File: `app.py:30-31`
Description: Schema criado no startup. Sem `flask-migrate` / Alembic.
Impact: Renomear coluna em produção não roda; schema diverge entre ambientes.
Recommendation: Introduzir `flask-migrate`; manter `create_all` só em dev/test.

### [LOW] DEPR-001 — `datetime.utcnow()`  (DEPR-001)
File: `models/task.py:15, 16`; `routes/task_routes.py:31, 72, 285`; `routes/user_routes.py:172`; `routes/report_routes.py:35, 45-46, 133`
Description: 9+ usos de `datetime.utcnow()`, deprecated desde Python 3.12.
Impact: Warnings em log; serão removidos em versão futura.
Recommendation: T-009 — `datetime.now(timezone.utc)`. Em SQLAlchemy `default=`, usar lambda.

### [LOW] DEPR-002 — `Model.query.get(id)`  (DEPR-002)
File: `routes/task_routes.py:67, 117, 123, 158, 189, 195, 228`; `routes/user_routes.py:29, 94, 117, 196`; `routes/report_routes.py:106, 159, 162, 191, 213`
Description: 16 usos de `Model.query.get(id)`, legacy desde SQLAlchemy 2.0.
Impact: Warning; será removido em versão futura.
Recommendation: T-009 — `db.session.get(Model, id)`.

### [LOW] DEPR-007 — `type(x) == list`  (DEPR-007)
File: `routes/task_routes.py:141, 210`; `utils/helpers.py:103`
Description: Comparação de tipo via igualdade ao invés de `isinstance`.
Impact: Não-pythonic; quebra com subclasses.
Recommendation: T-009 — `isinstance(x, list)`.

### [LOW] `print()` em vez de logging  (AP-301)
File: `routes/task_routes.py:149, 153, 219, 235`; `routes/user_routes.py:83, 89, 147`
Description: 7 chamadas a `print()` para registrar fluxo.
Impact: Sem níveis; sem destino configurável.
Recommendation: T-010 — `logging.getLogger(__name__)`.

### [LOW] Magic numbers em prioridade e tamanho  (AP-203)
File: `models/task.py:46-47` (priority 1..5), `routes/task_routes.py:113, 183` (priority 1..5), `utils/helpers.py:84, 110, 113-115` (`MIN_PASSWORD_LENGTH = 4`, `MAX_TITLE_LENGTH = 200`)
Description: `MIN_PASSWORD_LENGTH = 4` é absurdamente baixo; faixa de prioridade 1..5 hardcoded em 4 lugares.
Impact: Mudar política exige varrer o código.
Recommendation: T-010 — `config/constants.py` + `Enum` para prioridade.

### [LOW] Status como strings espalhadas  (AP-303)
File: 7+ arquivos: `task.py:39`, `task_routes.py:110, 177, 254-264`, `report_routes.py:19-22, 49, 60, 78-82, 121-128`, `user_routes.py:172-175`
Description: `'pending'`, `'in_progress'`, `'done'`, `'cancelled'` literais em 20+ lugares.
Impact: Typo silencioso quebra filtro.
Recommendation: T-010 — `TaskStatus(str, Enum)` em `config/constants.py`.

## APIs Deprecated

| ID | Local | Equivalente moderno |
|---|---|---|
| DEPR-001 | `datetime.utcnow()` em 9+ lugares | `datetime.now(timezone.utc)` |
| DEPR-002 | `Model.query.get(id)` em 16 lugares | `db.session.get(Model, id)` |
| DEPR-006 | `hashlib.md5()` para senha (`models/user.py:29,32`) | `bcrypt` |
| DEPR-007 | `type(x) == list` em 3 lugares | `isinstance(x, list)` |

================================
Total: 21 findings
Summary: CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 6
Critical-or-High count: 10   (≥1 required by acceptance criteria)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
