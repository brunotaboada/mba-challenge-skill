from typing import Optional

from src.database import get_db


_PRODUTO_COLUMNS = (
    "id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em",
)


def _row_to_dict(row) -> dict:
    return {col: row[col] for col in _PRODUTO_COLUMNS}


def listar() -> list[dict]:
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_por_id(produto_id: int) -> Optional[dict]:
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def criar(nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(produto_id: int, nome: str, descricao: str, preco: float,
              estoque: int, categoria: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, "
        "estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar(termo: str, categoria: Optional[str], preco_min: Optional[float],
           preco_max: Optional[float]) -> list[dict]:
    filtros = ["1 = 1"]
    params: list = []
    if termo:
        filtros.append("(nome LIKE ? OR descricao LIKE ?)")
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        filtros.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        filtros.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        filtros.append("preco <= ?")
        params.append(preco_max)
    query = f"SELECT * FROM produtos WHERE {' AND '.join(filtros)}"

    cursor = get_db().cursor()
    cursor.execute(query, params)
    return [_row_to_dict(row) for row in cursor.fetchall()]


def decrementar_estoque(cursor, produto_id: int, quantidade: int) -> None:
    cursor.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id),
    )
