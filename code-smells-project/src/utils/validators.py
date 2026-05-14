import re

from src.config.constants import CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def validate_email(email: str) -> None:
    if not email or not EMAIL_RE.match(email):
        raise ValidationError("Email inválido")


def validate_produto_payload(data: dict | None) -> dict:
    if not data:
        raise ValidationError("Dados inválidos")

    for required in ("nome", "preco", "estoque"):
        if required not in data:
            raise ValidationError(f"{required.capitalize()} é obrigatório")

    nome = data["nome"]
    preco = data["preco"]
    estoque = data["estoque"]
    descricao = data.get("descricao", "")
    categoria = data.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str) or len(nome) < NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}"
        )

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validate_usuario_payload(data: dict | None) -> dict:
    if not data:
        raise ValidationError("Dados inválidos")
    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "")
    if not nome:
        raise ValidationError("Nome é obrigatório")
    validate_email(email)
    if not senha or len(senha) < 6:
        raise ValidationError("Senha deve ter no mínimo 6 caracteres")
    return {"nome": nome, "email": email, "senha": senha}
