from flask import jsonify, request

from src.models import usuario as usuario_model
from src.utils.validators import ValidationError, validate_email, validate_usuario_payload


def listar():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def buscar(usuario_id: int):
    user = usuario_model.get_por_id(usuario_id)
    if not user:
        return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404
    return jsonify({"dados": user, "sucesso": True}), 200


def criar():
    payload = validate_usuario_payload(request.get_json())
    if usuario_model.get_por_email(payload["email"]):
        raise ValidationError("Email já cadastrado", status_code=409)
    novo_id = usuario_model.criar(payload["nome"], payload["email"], payload["senha"])
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    senha = data.get("senha") or ""
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    validate_email(email)
    user = usuario_model.autenticar(email, senha)
    if not user:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    return jsonify({"dados": user, "sucesso": True, "mensagem": "Login OK"}), 200
