import logging
from dataclasses import dataclass
from typing import Protocol

from src.models import pedido as pedido_model

log = logging.getLogger(__name__)


class EstoqueInsuficienteError(Exception):
    def __init__(self, produto_nome: str):
        super().__init__(f"Estoque insuficiente para {produto_nome}")
        self.produto_nome = produto_nome


class ProdutoInexistenteError(Exception):
    def __init__(self, produto_id: int):
        super().__init__(f"Produto {produto_id} não encontrado")
        self.produto_id = produto_id


@dataclass
class ItemPedido:
    produto_id: int
    quantidade: int


class Notifier(Protocol):
    def pedido_criado(self, usuario_id: int, pedido_id: int) -> None: ...
    def pedido_status_atualizado(self, pedido_id: int, status: str) -> None: ...


def criar_pedido(usuario_id: int, itens_raw: list[dict], notifier: Notifier) -> dict:
    itens = [ItemPedido(int(i["produto_id"]), int(i["quantidade"])) for i in itens_raw]

    total = 0.0
    with pedido_model.transaction() as cursor:
        for item in itens:
            cursor.execute(
                "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                (item.produto_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ProdutoInexistenteError(item.produto_id)
            if row["estoque"] < item.quantidade:
                raise EstoqueInsuficienteError(row["nome"])
            total += row["preco"] * item.quantidade

        pedido_id = pedido_model.criar_cabecalho(cursor, usuario_id, total)
        for item in itens:
            cursor.execute(
                "SELECT preco FROM produtos WHERE id = ?", (item.produto_id,)
            )
            preco = cursor.fetchone()["preco"]
            pedido_model.inserir_item(
                cursor, pedido_id, item.produto_id, item.quantidade, preco
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item.quantidade, item.produto_id),
            )

    notifier.pedido_criado(usuario_id, pedido_id)
    return {"pedido_id": pedido_id, "total": round(total, 2)}


def atualizar_status(pedido_id: int, novo_status: str, notifier: Notifier) -> None:
    pedido_model.atualizar_status(pedido_id, novo_status)
    notifier.pedido_status_atualizado(pedido_id, novo_status)
