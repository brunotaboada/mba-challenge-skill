from flask import Blueprint, jsonify, request

from schemas.category_schema import CreateCategorySchema, UpdateCategorySchema
from services import category_service

category_bp = Blueprint('categories', __name__)

_create_schema = CreateCategorySchema()
_update_schema = UpdateCategorySchema()


@category_bp.route('/categories', methods=['GET'])
def list_categories():
    return jsonify(category_service.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    payload = _create_schema.load(request.get_json() or {})
    return jsonify(category_service.create_category(payload)), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id: int):
    payload = _update_schema.load(request.get_json() or {})
    return jsonify(category_service.update_category(cat_id, payload)), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id: int):
    category_service.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
