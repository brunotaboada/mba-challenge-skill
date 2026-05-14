from typing import Optional

import bcrypt

from src.database import get_db


_PUBLIC_COLUMNS = ("id", "nome", "email", "tipo", "criado_em")


def _row_to_public_dict(row) -> dict:
    return {col: row[col] for col in _PUBLIC_COLUMNS}


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def listar() -> list[dict]:
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_public_dict(row) for row in cursor.fetchall()]


def get_por_id(usuario_id: int) -> Optional[dict]:
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return _row_to_public_dict(row) if row else None


def get_por_email(email: str) -> Optional[dict]:
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return None
    return {col: row[col] for col in row.keys()}


def criar(nome: str, email: str, plaintext_senha: str, tipo: str = "cliente") -> int:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hash_password(plaintext_senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email: str, plaintext_senha: str) -> Optional[dict]:
    row = get_por_email(email)
    if not row:
        return None
    if not verify_password(plaintext_senha, row["senha"]):
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
    }
