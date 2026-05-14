from flask import jsonify, request

from src.models import produto as produto_model
from src.utils.validators import ValidationError, validate_produto_payload


def listar():
    produtos = produto_model.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar(produto_id: int):
    produto = produto_model.get_por_id(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar():
    payload = validate_produto_payload(request.get_json())
    novo_id = produto_model.criar(**payload)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def atualizar(produto_id: int):
    if not produto_model.get_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    payload = validate_produto_payload(request.get_json())
    produto_model.atualizar(produto_id, **payload)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id: int):
    if not produto_model.get_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    produto_model.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_query():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min_raw = request.args.get("preco_min")
    preco_max_raw = request.args.get("preco_max")
    try:
        preco_min = float(preco_min_raw) if preco_min_raw else None
        preco_max = float(preco_max_raw) if preco_max_raw else None
    except ValueError as exc:
        raise ValidationError("preco_min/preco_max devem ser numéricos") from exc
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
