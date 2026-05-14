from flask import jsonify, request

from src.config.constants import PedidoStatus
from src.models import pedido as pedido_model
from src.services import pedido_service, relatorio_service
from src.services.notification_service import LoggingNotifier
from src.utils.validators import ValidationError

_notifier = LoggingNotifier()


def criar():
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id")
    itens = data.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    resultado = pedido_service.criar_pedido(usuario_id, itens, _notifier)
    return jsonify({"dados": resultado, "sucesso": True}), 201


def listar_todos():
    return jsonify({"dados": pedido_model.listar_todos(), "sucesso": True}), 200


def listar_por_usuario(usuario_id: int):
    return jsonify(
        {"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}
    ), 200


def atualizar_status(pedido_id: int):
    data = request.get_json() or {}
    novo_status = data.get("status", "")
    if novo_status not in PedidoStatus.values():
        raise ValidationError("Status inválido")
    pedido_service.atualizar_status(pedido_id, novo_status, _notifier)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    return jsonify(
        {"dados": relatorio_service.gerar_relatorio_vendas(), "sucesso": True}
    ), 200
