from flask import Blueprint, jsonify, request

from schemas.user_schema import CreateUserSchema, UpdateUserSchema
from services import user_service

user_bp = Blueprint('users', __name__)

_create_schema = CreateUserSchema()
_update_schema = UpdateUserSchema()


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    return jsonify(user_service.get_user(user_id)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    payload = _create_schema.load(request.get_json() or {})
    return jsonify(user_service.create_user(payload)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    payload = _update_schema.load(request.get_json() or {})
    return jsonify(user_service.update_user(user_id, payload)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    user_service.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id: int):
    return jsonify(user_service.get_user_tasks(user_id)), 200
