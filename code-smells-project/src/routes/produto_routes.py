from flask import Blueprint

from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_query, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto_controller.buscar, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produto_controller.atualizar, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produto_controller.deletar, methods=["DELETE"])
