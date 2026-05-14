from enum import Enum


class PedidoStatus(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


CATEGORIAS_VALIDAS = (
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
)

DESCONTO_FAIXAS = (
    (10000.0, 0.10),
    (5000.0, 0.05),
    (1000.0, 0.02),
)

NOME_MIN_LEN = 2
NOME_MAX_LEN = 200
