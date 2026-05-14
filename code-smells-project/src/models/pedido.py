from contextlib import contextmanager

from src.database import get_db


@contextmanager
def transaction():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("BEGIN")
    try:
        yield cursor
        db.commit()
    except Exception:
        db.rollback()
        raise


def criar_cabecalho(cursor, usuario_id: int, total: float) -> int:
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    return cursor.lastrowid


def inserir_item(cursor, pedido_id: int, produto_id: int, quantidade: int,
                 preco_unitario: float) -> None:
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
        "VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def atualizar_status(pedido_id: int, novo_status: str) -> None:
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def _hydrate(rows) -> list[dict]:
    pedidos: dict[int, dict] = {}
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


_BASE_SELECT = """
    SELECT
        p.id AS pedido_id,
        p.usuario_id,
        p.status,
        p.total,
        p.criado_em,
        ip.produto_id,
        ip.quantidade,
        ip.preco_unitario,
        pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr     ON pr.id = ip.produto_id
"""


def listar_todos() -> list[dict]:
    cursor = get_db().cursor()
    cursor.execute(_BASE_SELECT + " ORDER BY p.id")
    return _hydrate(cursor.fetchall())


def listar_por_usuario(usuario_id: int) -> list[dict]:
    cursor = get_db().cursor()
    cursor.execute(
        _BASE_SELECT + " WHERE p.usuario_id = ? ORDER BY p.id",
        (usuario_id,),
    )
    return _hydrate(cursor.fetchall())


def agregar_relatorio() -> dict:
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*)                                                AS total_pedidos,
            COALESCE(SUM(total), 0)                                 AS faturamento_bruto,
            SUM(CASE WHEN status = 'pendente'  THEN 1 ELSE 0 END)    AS pendentes,
            SUM(CASE WHEN status = 'aprovado'  THEN 1 ELSE 0 END)    AS aprovados,
            SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END)    AS cancelados
        FROM pedidos
        """
    )
    row = cursor.fetchone()
    return {
        "total_pedidos": row["total_pedidos"],
        "faturamento_bruto": row["faturamento_bruto"] or 0,
        "pendentes": row["pendentes"] or 0,
        "aprovados": row["aprovados"] or 0,
        "cancelados": row["cancelados"] or 0,
    }
