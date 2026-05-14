# MVC Guidelines — Estrutura Alvo

Esta referência define **o que a Fase 3 deve produzir**. Use junto com
`refactor-playbook.md` (que mostra como fazer cada transformação).

---

## Princípio

MVC para APIs HTTP, neste contexto, é uma **estratificação de responsabilidades**:

| Camada | Responsabilidade | O que NÃO pode |
|---|---|---|
| **Routes / Views** | mapear URL+verbo → controller. | conter `if`/loops/regra de negócio. |
| **Controllers** | parsear request, chamar service/model, montar response. | acessar banco diretamente, ter regra de negócio. |
| **Services** (opcional, recomendado) | regra de negócio, orquestração entre models, side-effects (email, pagamento, notificação). | lidar com HTTP. |
| **Models** | acesso a dados e mapeamento entidade ↔ banco. | conter HTTP, conter regra de negócio cross-entidade. |
| **Middlewares** | concerns transversais (auth, logging, validação, erro). | conter lógica de domínio. |
| **Config** | leitura de env, constantes globais. | I/O. |

Quando ficar em dúvida onde algo mora, aplique o teste: *"se eu trocasse de
framework HTTP, o que precisaria mudar?"* — só routes, controllers e
middlewares deveriam.

---

## Estrutura alvo — Python / Flask

```
<project>/
├── app.py                       # composition root: cria Flask, importa controllers, registra rotas e middlewares
├── .env.example                 # variáveis documentadas
├── requirements.txt
├── src/                         # (opcional, mas recomendado para projetos > 200 LOC)
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # SECRET_KEY, DEBUG, DATABASE_URL via os.environ
│   ├── models/
│   │   ├── __init__.py
│   │   ├── produto.py           # DAO ou SQLAlchemy Model
│   │   └── usuario.py
│   ├── services/                # camada opcional
│   │   ├── __init__.py
│   │   ├── pedido_service.py    # regra de criação de pedido, decremento de estoque
│   │   └── relatorio_service.py # agregações, cálculo de desconto
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── produto_controller.py
│   │   ├── usuario_controller.py
│   │   └── pedido_controller.py
│   ├── routes/                  # blueprints registrando os controllers
│   │   ├── __init__.py
│   │   ├── produto_routes.py
│   │   └── usuario_routes.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── error_handler.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
└── tests/                       # (opcional)
```

**Para projetos pequenos** (≤ 200 LOC), `src/` pode ser omitido e os módulos
ficam no root.

**Para Flask + SQLAlchemy** (já usado em `task-manager-api`):
- `db = SQLAlchemy()` fica em `src/extensions.py` ou `src/database.py`.
- `db.init_app(app)` no composition root.
- Models herdam de `db.Model`.

---

## Estrutura alvo — Node.js / Express

```
<project>/
├── src/
│   ├── app.js                   # cria app, registra middlewares e rotas
│   ├── server.js                # `app.listen(...)` separado do app
│   ├── config/
│   │   └── index.js             # process.env
│   ├── models/
│   │   ├── userModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   └── paymentModel.js
│   ├── services/
│   │   ├── checkoutService.js   # orquestra user/course/enrollment/payment
│   │   ├── paymentGateway.js    # adapter para gateway externo
│   │   └── reportService.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── userController.js
│   │   └── reportController.js
│   ├── routes/
│   │   ├── checkoutRoutes.js
│   │   ├── userRoutes.js
│   │   └── reportRoutes.js
│   ├── middlewares/
│   │   ├── errorHandler.js
│   │   └── validate.js
│   ├── db/
│   │   ├── connection.js        # cria/exporta instância sqlite
│   │   └── migrations.js        # schema inicial + seed em dev
│   └── utils/
│       └── crypto.js            # wrapper de bcrypt
├── .env.example
├── api.http
└── package.json
```

**Separar `app.js` de `server.js`**: o `app.js` exporta a app sem `listen()`,
o `server.js` chama `app.listen()`. Isso facilita testar com supertest.

---

## Regras invariantes (qualquer stack)

1. **Composition root único** — `app.py` ou `src/app.js`. Lê config, instancia
   services, registra rotas. Não contém regra.
2. **Nenhum segredo no fonte** — tudo via env, com `.env.example` documentando
   nomes e valores default seguros para dev.
3. **Modelo conhece dados, nada mais** — sem `print`/`console.log`, sem
   chamadas a outros models, sem HTTP.
4. **Controller ≤ 30 linhas por handler** — se passar, extraia para service.
5. **Error handling centralizado** — um middleware/error handler captura
   exceções do domínio, formata a resposta. Controllers podem subir exceção.
6. **Validação na borda** — schema (`marshmallow`/`pydantic`/`zod`/`joi`)
   antes do controller chamar o service.
7. **Sem estado global mutável** — caches, conexões, contadores devem viver
   em instâncias ou em factories, não em variáveis de módulo.
8. **Endpoints preservados** — paths + verbos da API antes e depois precisam
   bater. Renomear endpoint requer aprovação explícita do usuário.

---

## Decisões de design recorrentes

### Quando criar `services/`?

- Há regra de negócio orquestrando 2+ models? → service.
- Há side-effect (email, pagamento)? → service.
- Há agregação ou cálculo derivado? → service.
- Se nada disso, controller pode chamar model direto (CRUD simples).

### Quando `routes/` separado de `controllers/`?

- Em Flask, blueprints unem rotas+controllers naturalmente. Aceitável manter
  ambos no mesmo arquivo se o blueprint tem ≤ 5 rotas.
- Em Express, separe `routes/` (define o `router`) de `controllers/` (define
  as funções handler). Isso permite que rotas declarem middlewares de auth/
  validação sem repetição.

### O que vai no `utils/`?

Funções **puras** sem dependência do framework:
- formatação de data
- validador de CPF/email/Luhn
- helpers de string

O que **não vai no utils**:
- I/O
- regra de negócio (vai em service)
- acesso a banco (vai em model)
- side-effects

### Banco de dados

- **SQLite cru** (`sqlite3` em Python ou Node): sempre parametrize. Crie um
  `db/connection.py` que retorne uma `connection` request-scoped, não global.
- **ORM**: use o método não-deprecated (`db.session.get` em SQLAlchemy 2.0,
  `findByPk` em Sequelize, etc.).
- **Migrations**: se já existe schema inline (`db.create_all`/`db.run("CREATE TABLE")`),
  mantenha por enquanto, mas adicione um `TODO` no `app.py` para migrar para
  Alembic/Umzug.

---

## Anti-checklist (sinais de que a refatoração não está pronta)

- [ ] Alguma string `SECRET_KEY = "..."` (ou similar) no fonte
- [ ] Algum `cursor.execute("..." + var)` ou `db.run(\`...${var}\`)`
- [ ] Senha aparecendo em `jsonify`/`res.json`
- [ ] Função de rota com > 50 linhas
- [ ] Classe que faz banco + roteamento + regra
- [ ] `print()` ou `console.log` para logar fluxo
- [ ] `except:` bare em Python; `catch (_) {}` em Node
- [ ] `datetime.utcnow()`, `Model.query.get`, `hashlib.md5` para senha

Se algum sobrou, a Fase 3 não acabou.
