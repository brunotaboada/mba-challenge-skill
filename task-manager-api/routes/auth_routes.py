from flask import Blueprint, jsonify, request

from schemas.user_schema import LoginSchema
from services import auth_service

auth_bp = Blueprint('auth', __name__)
_login_schema = LoginSchema()


@auth_bp.route('/login', methods=['POST'])
def login():
    payload = _login_schema.load(request.get_json() or {})
    return jsonify(auth_service.login(payload['email'], payload['password'])), 200
