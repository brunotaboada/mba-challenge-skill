from flask import Blueprint, jsonify, request

from schemas.task_schema import CreateTaskSchema, UpdateTaskSchema
from services import task_service

task_bp = Blueprint('tasks', __name__)

_create_schema = CreateTaskSchema()
_update_schema = UpdateTaskSchema()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_service.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id: int):
    return jsonify(task_service.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    payload = _create_schema.load(request.get_json() or {})
    return jsonify(task_service.create_task(payload)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id: int):
    payload = _update_schema.load(request.get_json() or {})
    return jsonify(task_service.update_task(task_id, payload)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id: int):
    task_service.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify(
        task_service.search_tasks(
            q=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=request.args.get('priority', ''),
            user_id=request.args.get('user_id', ''),
        )
    ), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_service.task_stats()), 200
