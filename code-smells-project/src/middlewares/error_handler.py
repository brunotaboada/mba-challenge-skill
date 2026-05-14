import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from src.services.pedido_service import EstoqueInsuficienteError, ProdutoInexistenteError
from src.utils.validators import ValidationError

log = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def _validation(err: ValidationError):
        return jsonify({"erro": str(err), "sucesso": False}), err.status_code

    @app.errorhandler(EstoqueInsuficienteError)
    def _estoque(err: EstoqueInsuficienteError):
        return jsonify({"erro": str(err), "sucesso": False}), 400

    @app.errorhandler(ProdutoInexistenteError)
    def _produto(err: ProdutoInexistenteError):
        return jsonify({"erro": str(err), "sucesso": False}), 404

    @app.errorhandler(HTTPException)
    def _http(err: HTTPException):
        return jsonify({"erro": err.description, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        log.exception("Unhandled exception")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
