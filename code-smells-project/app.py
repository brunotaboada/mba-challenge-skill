"""Composition root da API de E-commerce.

Cria a app Flask, lê a configuração do ambiente, registra os blueprints
(produtos, usuários, pedidos) e o error handler centralizado. Toda a regra
de negócio vive em `src/services/`, o acesso a dados em `src/models/` e a
configuração em `src/config/`.
"""
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from src.config.settings import settings
from src.database import init_schema, register_db_lifecycle
from src.middlewares.error_handler import register_error_handlers
from src.routes.pedido_routes import pedido_bp
from src.routes.produto_routes import produto_bp
from src.routes.usuario_routes import usuario_bp


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> Flask:
    _configure_logging()
    init_schema()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app, origins=settings.ALLOWED_ORIGINS)
    register_db_lifecycle(app)
    register_error_handlers(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": settings.VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "ok",
            "versao": settings.VERSION,
        })

    return app


app = create_app()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Servidor iniciado em http://%s:%d", settings.HOST, settings.PORT
    )
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
