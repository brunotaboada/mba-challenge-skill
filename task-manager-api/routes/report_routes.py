from flask import Blueprint, jsonify

from services import report_service

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_service.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id: int):
    data = report_service.user_report(user_id)
    if data is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(data), 200
