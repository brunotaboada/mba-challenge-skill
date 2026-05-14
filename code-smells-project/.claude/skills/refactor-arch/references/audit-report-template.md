# Template do Relatório de Auditoria (Fase 2)

Use **exatamente** este formato. Substitua os campos `<...>` pelos valores reais.
Imprima na tela durante a Fase 2 **e** salve uma cópia em `../reports/audit-<project-folder>.md`.

---

## Cabeçalho

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <Linguagem> + <Framework + versão>
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <YYYY-MM-DD>
```

## Resumo

```
## Summary
CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>
Total: <N> findings
```

## Findings (uma seção por finding, numerados, ordenados por severidade)

```
### [<SEVERIDADE>] <Categoria>  (<AP-ID>)
File: <caminho/relativo/arquivo.ext>:<linha>  ou  <arquivo.ext>:<linha-inicial>-<linha-final>
Description: <1-3 frases descrevendo objetivamente o problema>
Impact: <consequência concreta — segurança, performance, manutenção>
Recommendation: <ação imediata — pode citar a transformação do playbook>
```

Regras:

- `<SEVERIDADE>` é uma de: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- `<AP-ID>` é o ID do catálogo (`AP-001`, `DEPR-002`, etc.).
- `File:` sempre tem coordenadas. Se for um intervalo, use `start-end`. Se forem múltiplas ocorrências, prefira listar até 5 linhas: `file.py:10, 24, 89, 112`.
- Não inclua trechos longos de código no relatório — só descrição e linha.

## Seção obrigatória — APIs deprecated

Mesmo se vazia, **sempre** inclua esta subseção logo após os findings:

```
## APIs Deprecated
<lista de findings DEPR-* — ou "Nenhuma API deprecated detectada.">
```

## Fechamento

```
================================
Total: <N> findings
Summary: CRITICAL: <a> | HIGH: <b> | MEDIUM: <c> | LOW: <d>
Critical-or-High count: <a + b>   (≥1 required by acceptance criteria)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Exemplo completo (referência)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-05-14

## Summary
CRITICAL: 9 | HIGH: 5 | MEDIUM: 4 | LOW: 3
Total: 21 findings

## Findings

### [CRITICAL] Hardcoded Secret  (AP-001)
File: app.py:7
Description: SECRET_KEY definido em literal no código: "minha-chave-super-secreta-123".
Impact: Segredo no histórico do Git é vazamento permanente. Permite assinar/forjar sessões/JWTs.
Recommendation: Mover para os.environ.get("SECRET_KEY"); adicionar .env.example.

### [CRITICAL] SQL Injection  (AP-002)
File: models.py:28, 47-50, 92, 109-110, 127-128, 148-150, 280-281, 289-298
Description: Praticamente toda função monta SQL via concatenação com input do usuário (login, busca de produto, criação de pedido). Exemplo: SELECT ... WHERE email = '" + email + "' AND senha = '" + senha + "'.
Impact: Bypass de login com `admin' OR '1'='1`; dump de tabela; potencial drop.
Recommendation: Parametrizar — cursor.execute("... WHERE id = ?", (id,)).

### [CRITICAL] DB-wipe sem autenticação  (AP-005)
File: app.py:47-57
Description: Endpoint POST /admin/reset-db apaga itens_pedido, pedidos, produtos e usuarios. Sem auth, sem CSRF, sem role check.
Impact: Qualquer ator com a URL apaga o banco inteiro.
Recommendation: Remover o endpoint; reset deve ser comando CLI separado, fechado em ambiente.

### [HIGH] God Module  (AP-101)
File: models.py:1-314
Description: Arquivo único contém DAO de 4 entidades + lógica de criação de pedido + cálculo de relatório de vendas com regra de desconto inline.
Impact: Impossível testar em isolamento; mudanças se propagam.
Recommendation: Separar em models/<entidade>.py + services/pedido_service.py + services/relatorio_service.py.

### [MEDIUM] N+1 Query  (AP-201)
File: models.py:186-200, 219-232
Description: get_pedidos_usuario e get_todos_pedidos abrem cursores aninhados (cursor2, cursor3) para buscar itens e nome do produto por linha de pedido.
Impact: Latência cresce com tamanho da listagem; perceptível com >100 pedidos.
Recommendation: JOIN único entre pedidos, itens_pedido e produtos; ou WHERE id IN (...) em lote.

### [LOW] print() como logging  (AP-301)
File: controllers.py:8, 11, 57, 61, 106, 179, 182, 208-210, 219, 248-251
Description: 14 chamadas a print() para logar fluxo da aplicação.
Impact: Sem níveis, sem formatação estruturada, sem controle de destino.
Recommendation: Migrar para logging.getLogger(__name__) com handler configurado em app.py.

## APIs Deprecated
Nenhuma API deprecated detectada neste projeto.

================================
Total: 6 findings (exemplo abreviado; o real teria 21)
Summary: CRITICAL: 3 | HIGH: 1 | MEDIUM: 1 | LOW: 1
Critical-or-High count: 4   (≥1 required by acceptance criteria)
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
