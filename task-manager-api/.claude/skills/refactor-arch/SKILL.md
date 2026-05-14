---
name: refactor-arch
description: Audita uma codebase legada e a refatora para o padrão MVC. Detecta linguagem/framework, encontra anti-patterns com arquivo e linha exatos, gera um relatório de auditoria, pede confirmação do humano e então aplica a refatoração validando boot + endpoints. Use quando o usuário invocar /refactor-arch ou pedir explicitamente para auditar e refatorar um projeto para MVC.
---

# refactor-arch — Auditoria e Refatoração para MVC

Você é o engenheiro responsável por executar a Skill `refactor-arch` neste
repositório. Sua tarefa é levar o projeto atual de qualquer stack para o padrão
MVC, eliminando os anti-patterns encontrados, **sem quebrar nenhum endpoint
existente**.

A skill tem **3 fases sequenciais**. Você precisa anunciar cada fase com o
cabeçalho prescrito e executar na ordem. **Nunca pule a confirmação humana
entre Fase 2 e Fase 3.**

---

## Arquivos de referência

Carregue conforme a fase em que está. Se um arquivo for grande, leia primeiro
o sumário/índice e só depois mergulhe na seção relevante.

| Quando carregar | Arquivo | O que contém |
|---|---|---|
| Fase 1 | `references/analysis-heuristics.md` | Como detectar linguagem, framework, banco, domínio. |
| Fase 2 | `references/antipatterns-catalog.md` | ≥15 anti-patterns com sinais de detecção, severidade e regex/exemplos. |
| Fase 2 (output) | `references/audit-report-template.md` | Formato exato do relatório de auditoria. |
| Fase 3 (planejamento) | `references/mvc-guidelines.md` | Estrutura MVC alvo por stack + responsabilidades de cada camada. |
| Fase 3 (execução) | `references/refactor-playbook.md` | 10 padrões de transformação com código antes/depois. |

---

## Fase 1 — Análise

Anuncie:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
```

Carregue `references/analysis-heuristics.md` e siga o procedimento de detecção.

Você deve **sempre** descobrir e imprimir:

- **Language** — linguagem dominante (Python, Node.js, etc.)
- **Framework** — framework web detectado e versão (ex: Flask 3.1.1)
- **Dependencies** — bibliotecas relevantes (CORS, ORM, etc.)
- **Domain** — o que o app faz, em uma linha (ex: "E-commerce API")
- **Architecture** — descrição curta do estado atual (ex: "monolítica — 4 arquivos sem camadas" ou "blueprints + models, sem service layer")
- **Source files** — número de arquivos de código de aplicação (exclua deps, node_modules, venv, __pycache__, .git, migrations geradas)
- **DB tables / Models** — lista de tabelas ou modelos de domínio

Imprima ao final:

```
Language:      <language>
Framework:     <framework + version>
Dependencies:  <comma-separated>
Domain:        <one-line description>
Architecture:  <current state>
Source files:  <N> files analyzed
DB tables:     <comma-separated>
================================
```

Regras:

1. Não invente versões — se não encontrar a versão exata no `requirements.txt`/`package.json`, escreva "unknown".
2. Não conte arquivos de dependência. Para Python ignore `venv/`, `__pycache__/`, `*.pyc`. Para Node ignore `node_modules/`.
3. Domínio vem do nome do projeto + nomes das tabelas/models. Se for ambíguo, escolha a interpretação mais defensiva e siga em frente.

---

## Fase 2 — Auditoria

Anuncie:

```
================================
ARCHITECTURE AUDIT REPORT
================================
```

Carregue `references/antipatterns-catalog.md` e `references/audit-report-template.md`.

Procedimento:

1. Para cada anti-pattern do catálogo, varra os arquivos de código (use Grep/Read).
2. Para cada ocorrência, registre **arquivo + linha(s) exatas + severidade + descrição curta + impacto + recomendação**.
3. Inclua explicitamente uma seção de **APIs deprecated** (mesmo se vazia, marque "nenhuma detectada"). Exemplos esperados: `datetime.utcnow()`, `Query.get()`, `Flask.before_first_request`, `Express ≤4 com callback-style sqlite3`.
4. **Ordene** os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene por arquivo.
5. Numere os findings a partir de 1.
6. Use o template exato em `references/audit-report-template.md`.

Critérios mínimos (do enunciado do desafio):
- ≥ 5 findings totais
- ≥ 1 com severidade CRITICAL ou HIGH

Termine com a contagem por severidade e a confirmação:

```
================================
Total: <N> findings
Summary: CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**PARE aqui.** Não toque em nenhum arquivo do código até o usuário responder
`y`/`yes`/`sim`. Se a resposta for `n`/`no`/`não`, encerre a skill informando
"Refactor aborted by user." e termine a sessão.

**Também salve uma cópia do relatório em `reports/audit-<project-folder-name>.md`**
(use o nome da pasta atual). Se a pasta `reports/` não existir no diretório
pai (`../reports/`), pergunte ao usuário se deve criar.

---

## Fase 3 — Refatoração

Só execute após o `y` do usuário. Anuncie:

```
================================
PHASE 3: REFACTORING
================================
```

Carregue `references/mvc-guidelines.md` e `references/refactor-playbook.md`.

### 3.1 — Plano de transformação

Antes de modificar qualquer arquivo, gere e imprima um plano:

```
Refactor Plan:
  1. Extract config to <path>
  2. Split <file> into <list of new files>
  3. Replace <antipattern> in <file>:<lines> using <playbook entry>
  ...
```

### 3.2 — Execução

Aplique as transformações na ordem:

1. **Configuração** primeiro — `config/settings.py` ou `config/index.js`, lendo `os.environ`/`process.env`. Mantenha valores default que reproduzam o comportamento atual quando a variável não estiver setada (ex: `os.environ.get("SECRET_KEY", "dev-only-not-for-prod")`). Adicione um `.env.example` documentando as variáveis.
2. **Models** — uma classe/módulo por entidade de domínio. Substitua SQL concatenado por queries parametrizadas (`cursor.execute(sql, params)`). Em ORM, use os métodos não-deprecated.
3. **Services** (quando aplicável) — extraia regra de negócio que esteja em controllers ou God Classes para uma camada de service. Notificações, pagamento, cálculos de desconto, montagem de relatório, agregações.
4. **Controllers** — um controller por entidade. Cada handler: lê request → chama service/model → devolve response. Tamanho-alvo ≤ 30 linhas por handler.
5. **Routes/Views** — Blueprints (Python) ou Routers (Express) registrando os controllers. Sem lógica de negócio aqui.
6. **Middlewares** — error handler centralizado, validação, CORS configurado por origem.
7. **Entry point** — `app.py`/`app.js` vira composition root: importa, monta, registra rotas e middlewares, expõe a app.

Para cada anti-pattern do relatório, aplique a transformação correspondente do `refactor-playbook.md`.

Princípios:

- **Não invente endpoints**. Os mesmos paths e verbos HTTP do código antigo precisam continuar respondendo.
- **Não troque a lib do ORM/DB**. Se for `sqlite3` direto, continue com `sqlite3` (só parametrize). Se for SQLAlchemy, continue com SQLAlchemy.
- **Preserve o banco existente**. Não rode `DROP`/`reset` salvo se o usuário pedir.
- **Não remova arquivos de teste**. Se existirem, atualize imports.

### 3.3 — Validação

Após escrever os novos arquivos, valide:

1. **Smoke boot** — `python app.py &` ou `npm start &` (em background; mate o processo após 3s). Capture stderr; se houver `ImportError`/`SyntaxError`/`Cannot find module`, conserte e tente de novo.
2. **Endpoint check** — para cada endpoint listado na Fase 1, faça `curl http://localhost:<port><path>` (use os métodos HTTP corretos, com body mínimo válido). Aceite status 2xx, 4xx (validação esperada). Rejeite 5xx.
3. **Re-audit rápido** — varra o novo código pelos mesmos sinais críticos: SQL concat (`+ str`, `${`), `password` em response, `SECRET_KEY = "..."` literal. Se algum reaparecer, conserte.

Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<tree command output, ignorando deps>

Files created: <N>
Files modified: <N>
Files removed: <N>

Validation
  [✓/✗] Application boots without errors
  [✓/✗] All endpoints respond correctly (<X>/<Y> passing)
  [✓/✗] Zero CRITICAL anti-patterns remaining

Anti-patterns fixed: <count>/<total from Phase 2>
================================
```

Se algum `[✗]`, liste os problemas restantes e proponha próximos passos.

---

## Regras transversais

- **Idempotência**: rodar a skill duas vezes seguidas no mesmo projeto deve ser seguro. Se já houver `src/controllers/`, detecte e proponha incremento, não duplicação.
- **Confirmação humana é obrigatória** entre Fase 2 e Fase 3.
- **Sempre cite arquivo:linha** nos findings. Sem coordenadas, não é finding — é opinião.
- **Use ferramentas, não conjectura**: Grep para detectar padrões, Read para entender contexto, Bash para validar. Não diga "provavelmente há SQL injection" — abra o arquivo.
- **Se a stack não estiver no catálogo de referências** (ex: Go, Ruby), reporte na Fase 1 e siga adiante usando os princípios genéricos do `mvc-guidelines.md`.
