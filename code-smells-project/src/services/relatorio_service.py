from src.config.constants import DESCONTO_FAIXAS
from src.models import pedido as pedido_model


def _calcular_desconto(faturamento: float) -> float:
    for limite, taxa in DESCONTO_FAIXAS:
        if faturamento > limite:
            return faturamento * taxa
    return 0.0


def gerar_relatorio_vendas() -> dict:
    aggregate = pedido_model.agregar_relatorio()
    faturamento = float(aggregate["faturamento_bruto"])
    desconto = _calcular_desconto(faturamento)
    total = aggregate["total_pedidos"]

    return {
        "total_pedidos": total,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": aggregate["pendentes"],
        "pedidos_aprovados": aggregate["aprovados"],
        "pedidos_cancelados": aggregate["cancelados"],
        "ticket_medio": round(faturamento / total, 2) if total > 0 else 0,
    }
